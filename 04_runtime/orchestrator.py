"""Veil Town orchestrator — wires all subsystems into a single agent turn.

Pipeline per run_once():
1. Generate output via `llm_provider.generate_agent_output` (Ollama HTTP; event-aware revision)
2. Score via 05_alignment/scorer
3. Canon enforcement via canon_enforcer
4. Quarantine check via 05_alignment/quarantine (hard canon OR drift exceeds gates → quarantine + abort)
5. Write memory via memory_router
6. Tick event engine + optionally generate dream
7. Update relationship via memory_router.update_relationship (delta + DSSM physics summary)
8. Send agent message via agent_comms
9. Append enriched event to 06_logs/replay.jsonl
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path

from veil_loader import load_module

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

LOG_PATH = _ROOT / "06_logs" / "replay.jsonl"

# Sibling-module loading via cache-safe loader
memory_router = load_module("memory_router", _ROOT / "03_memory" / "memory_router.py")
scorer = load_module("scorer", _ROOT / "05_alignment" / "scorer.py")
quarantine = load_module("quarantine", _ROOT / "05_alignment" / "quarantine.py")
canon_enforcer_mod = load_module("canon_enforcer", _HERE / "canon_enforcer.py")
agent_comms_mod = load_module("agent_comms", _HERE / "agent_comms.py")
event_engine_mod = load_module("event_engine", _HERE / "event_engine.py")
llm_provider = load_module("llm_provider", _HERE / "llm_provider.py")
unlock_engine = load_module(
    "unlock_engine", _ROOT / "01_districts" / "unlock_engine.py"
)
persona_router = load_module("persona_router", _HERE / "persona_router.py")
semantic_scorer_mod = load_module(
    "semantic_scorer", _ROOT / "05_alignment" / "semantic_scorer.py"
)
image_provider = load_module("image_provider", _HERE / "image_provider.py")
voice_provider = load_module("voice_provider", _HERE / "voice_provider.py")
intent_classifier = load_module("intent_classifier", _HERE / "intent_classifier.py")

# Process-wide semantic scorer instance (reference vectors cached after first use)
_SEMANTIC_SCORER: object | None = None


def _derive_voice_tags(
    score: object, intent_info: dict | None, veil_state: str
) -> list[str]:
    tags: set[str] = {"mystery"}
    if getattr(score, "prism_resonance", 0.0) >= 0.4:
        tags.add("warmth")
    if getattr(score, "dark_quasar_resonance", 0.0) >= 0.4:
        tags.add("quasar")
    if getattr(score, "emotional_depth", 0.0) >= 0.4:
        tags.add("depth")

    intent_label = (intent_info or {}).get("label")
    if intent_label in {"deep", "emotional"}:
        tags.add("intimacy")
    if intent_label in {"challenging", "hostile"}:
        tags.add("boundary")
    if veil_state == "storm":
        tags.add("sharpness")
    if veil_state == "quasar_active":
        tags.add("dream")
    return sorted(tags)


def _depth_delta(score: object, intent_info: dict | None) -> float:
    base_depth_delta = (getattr(score, "emotional_depth", 0.0) - 0.3) * 0.1
    intent_boost = (
        (intent_info or {}).get("depth_modifier", 0.0) * 0.02 if intent_info else 0.0
    )
    return max(-0.10, min(0.10, base_depth_delta + intent_boost))


def _event_descriptions(events: list[object], limit: int = 2) -> list[str]:
    descriptions: list[str] = []
    seen: set[str] = set()
    for event in events[:limit]:
        payload = getattr(event, "payload", {}) or {}
        description = (
            payload.get("description")
            or payload.get("object")
            or getattr(event, "event_id", "")
        )
        if not description:
            continue
        description = str(description).strip()
        if description and description not in seen:
            seen.add(description)
            descriptions.append(description)
    return descriptions


def _event_revision_prompt(
    base_prompt: str, current_output: str, preview_events: list[object]
) -> str:
    descriptions = _event_descriptions(preview_events)
    if not descriptions:
        return base_prompt
    event_lines = "\n".join(f"- {description}" for description in descriptions)
    return (
        f"{base_prompt}\n\n"
        "Current symbolic pressure in the scene:\n"
        f"{event_lines}\n\n"
        f"Draft response: {current_output}\n\n"
        "Revise the response so it naturally reacts to this scene pressure. "
        "Stay in character and avoid referring to events as a system or checklist."
    )


def _blend_event_context(output: str, preview_events: list[object]) -> str:
    descriptions = _event_descriptions(preview_events, limit=1)
    if not descriptions:
        return output
    primary = descriptions[0]
    if primary.lower() in output.lower():
        return output
    return f"{output} {primary}"


def _maybe_generate_voice(
    agent_id: str,
    text: str,
    veil_state: str,
    emotional_tags: list[str],
    emotional_depth: float,
) -> dict | None:
    """Gated by VEIL_GENERATE_VOICE=1. Always queue-safe."""
    if os.environ.get("VEIL_GENERATE_VOICE", "0") not in ("1", "true", "True"):
        return None
    try:
        return voice_provider.generate_voice(
            agent_id,
            text,
            emotional_tone="warm-mysterious",
            veil_state=veil_state,
            emotional_tags=emotional_tags,
            emotional_depth=emotional_depth,
        )
    except Exception as e:
        return {"error": str(e)}


def _maybe_generate_image(
    agent_id: str, player_state: dict, veil_state: str
) -> dict | None:
    """Gated by VEIL_GENERATE_IMAGES=1. Picks the deepest-unlocked district
    as the current scene; falls back to caetherra. Always queue-safe.
    """
    if os.environ.get("VEIL_GENERATE_IMAGES", "0") not in ("1", "true", "True"):
        return None
    districts = player_state.get("unlocked_districts") or ["caetherra"]
    # Prefer the most recently unlocked district as "current scene"
    district = districts[-1] if districts else "caetherra"
    try:
        return image_provider.generate_scene_image(
            agent_id=agent_id, district=district, veil_state=veil_state
        )
    except Exception as e:
        return {"error": str(e)}


def _maybe_semantic_blend(score_dict: dict, text: str) -> dict:
    """Optionally blend lexical scores with semantic embedding similarity.

    Gated by VEIL_USE_SEMANTIC=1. Falls through silently if Ollama is offline
    or the embed model is unavailable. Blends three axes:
    prism_resonance, dark_quasar_resonance, emotional_depth.
    Lexical:semantic weight is 0.5:0.5 — semantic is no more trusted than
    lexical until calibrated. Adds `_semantic` key to the result for traces.
    """
    if os.environ.get("VEIL_USE_SEMANTIC", "0") not in ("1", "true", "True"):
        return score_dict
    global _SEMANTIC_SCORER
    if _SEMANTIC_SCORER is None:
        _SEMANTIC_SCORER = semantic_scorer_mod.SemanticScorer()
    try:
        sem = _SEMANTIC_SCORER.score(text)  # type: ignore[attr-defined]
    except Exception:
        sem = None
    if not sem:
        return score_dict
    blended = dict(score_dict)
    for lex_key, sem_key in (
        ("prism_resonance", "prism"),
        ("dark_quasar_resonance", "dark_quasar"),
        ("emotional_depth", "depth"),
    ):
        if sem_key in sem and lex_key in blended:
            blended[lex_key] = 0.5 * blended[lex_key] + 0.5 * float(sem[sem_key])
    blended["_semantic"] = sem
    return blended


# Districts to check for runtime unlock (caetherra is always unlocked at start)
_LOCKABLE_DISTRICTS = ("ashveil", "ember_vaults", "stillward", "the_hollow")
_VEIL_ORDER = ("calm", "still", "storm", "quasar_active")
_CANON_REFS = ["VEIL-001", "VEIL-002"]


def _capture_player_intent(player_input: str | None, target_agent: str) -> dict | None:
    if not player_input:
        return None
    memory_router.write_memory(
        "private",
        player_input,
        agent_id=target_agent,
        emotional_tags=["player_input"],
        canon_refs=[],
    )
    try:
        return intent_classifier.classify_intent(player_input)
    except Exception as e:
        return {"label": "unclear", "depth_modifier": 0.0, "error": str(e)}


def _build_user_prompt(player_input: str | None) -> str | None:
    if not player_input:
        return None
    return (
        f'The player just said to you: "{player_input}"\n\n'
        "Respond as the agent. One short, in-voice utterance (2-4 sentences). "
        "React to what they said. Stay in character."
    )


def _generate_with_event_revision(
    agent_id: str,
    user_prompt: str | None,
    engine: object,
    current_player_state: dict,
    intent_info: dict | None,
) -> tuple[str, dict, list]:
    llm_result = llm_provider.generate_agent_output(agent_id, user_prompt=user_prompt)
    output = llm_result["output"]

    preview_score = scorer.score_text(
        output,
        agent_id=agent_id,
        canon_refs=_CANON_REFS,
    )
    projected_depth = max(
        0.0,
        min(
            1.0,
            current_player_state.get("emotional_depth", 0.0)
            + _depth_delta(preview_score, intent_info),
        ),
    )
    preview_events = engine.preview_events(projected_depth, limit=2)
    if preview_events:
        revised_prompt = _event_revision_prompt(
            user_prompt or "Speak now to the player.", output, preview_events
        )
        revised_result = llm_provider.generate_agent_output(
            agent_id, user_prompt=revised_prompt
        )
        output = revised_result["output"]
        if revised_result.get("fallback", False):
            output = _blend_event_context(output, preview_events)
            revised_result = {**revised_result, "output": output}
        llm_result = revised_result

    llm_meta = {
        "model": llm_result.get("model"),
        "fallback": llm_result.get("fallback", False),
    }
    if preview_events:
        llm_meta["event_preview"] = [
            getattr(event, "event_id", "") for event in preview_events
        ]
    if llm_result.get("error"):
        llm_meta["error"] = llm_result["error"]
    return output, llm_meta, preview_events


def _score_output(output: str, agent_id: str) -> tuple[object, dict]:
    score = scorer.score_text(
        output,
        agent_id=agent_id,
        canon_refs=_CANON_REFS,
    )
    return score, _maybe_semantic_blend(score.to_dict(), output)


def _enforce_canon(output: str, agent_id: str) -> tuple[list, bool, str | None]:
    try:
        enforcer = canon_enforcer_mod.CanonEnforcer()
        canon_results = enforcer.enforce(output, agent_id)
        hard_violation = any(
            getattr(r, "severity", "soft") == "hard" and getattr(r, "violated", False)
            for r in canon_results
        )
    except Exception as e:
        return [], False, str(e)
    return canon_results, hard_violation, None


def _quarantine_event(
    *,
    agent_id: str,
    output: str,
    llm_meta: dict,
    score_dict: dict,
    current_veil: str,
    hard_violation: bool,
    should_q: bool,
    q_reason: str,
) -> dict:
    reason = q_reason if should_q else "hard canon violation"
    try:
        q_id = quarantine.quarantine_output(
            agent_id=agent_id,
            content=output,
            reason=reason,
            alignment_score=score_dict,
            veil_state=current_veil,
            canon_refs=_CANON_REFS,
            emotional_tags=["warmth", "mystery"],
        )
    except Exception as e:
        q_id = None
        reason = f"{reason} (quarantine write failed: {e})"
    return {
        "agent": agent_id,
        "action": "quarantined",
        "quarantine_id": q_id,
        "reason": reason,
        "output": output,
        "llm": llm_meta,
        "alignment": score_dict,
    }


def _tick_events_and_dream(
    engine: object,
    agent_id: str,
    accumulated_depth: float,
) -> tuple[list, str | None, object | None, dict | None]:
    try:
        events_fired = engine.tick(accumulated_depth, agent_id)
    except Exception as e:
        return [], str(e), None, None

    dream = None
    dream_alignment: dict | None = None
    if accumulated_depth > 0.4:
        try:
            dream = engine.generate_dream(
                agent_id,
                accumulated_depth,
                llm_callable=lambda aid, p: llm_provider.generate_agent_output(
                    aid, user_prompt=p
                ),
            )
        except Exception as e:
            dream = {"error": str(e)}

    dream_succeeded = dream is not None and not isinstance(dream, dict)
    if dream_succeeded:
        try:
            dream_score = scorer.score_text(
                dream.content,
                agent_id=agent_id,
                canon_refs=_CANON_REFS,
            )
            dream_score_dict = _maybe_semantic_blend(
                dream_score.to_dict(), dream.content
            )
            dream_score_dict["emotional_tags"] = ["dream", "bypass"]
            dream_score_dict["dream_type"] = dream.dream_type
            dream_alignment = dream_score_dict
        except Exception as e:
            dream_alignment = {"error": str(e)}
    return events_fired, None, dream, dream_alignment


def _resolve_veil_state(
    prior_veil: str, accumulated_depth: float
) -> tuple[str, str | None]:
    if accumulated_depth >= 0.85:
        new_veil = "quasar_active"
    elif accumulated_depth >= 0.55:
        new_veil = "storm"
    elif accumulated_depth >= 0.25:
        new_veil = "still"
    else:
        new_veil = prior_veil
    if new_veil != prior_veil and _VEIL_ORDER.index(new_veil) > _VEIL_ORDER.index(
        prior_veil
    ):
        return new_veil, f"{prior_veil}->{new_veil}"
    return prior_veil, None


def _record_narrative_beats(
    *,
    agent_id: str,
    target_agent: str,
    output: str,
    dream: object | None,
    accumulated_depth: float,
    player_state: dict,
) -> list[str]:
    beats_fired: list[str] = []
    if memory_router.record_beat(
        "first_contact",
        agent_id,
        payload={"target": target_agent, "output": output[:120]},
    ):
        beats_fired.append(f"first_contact:{agent_id}")
    dream_succeeded = dream is not None and not isinstance(dream, dict)
    if dream_succeeded and memory_router.record_beat(
        "first_dream",
        getattr(dream, "dream_type", "dream"),
        payload={"agent": agent_id, "depth": accumulated_depth},
    ):
        beats_fired.append(f"first_dream:{getattr(dream, 'dream_type', 'dream')}")
    if player_state.get("emotional_depth", 0) >= 0.5 and memory_router.record_beat(
        "depth_threshold", "halfway", payload={"turns": player_state["turns_taken"]}
    ):
        beats_fired.append("depth_threshold:halfway")
    if player_state.get("emotional_depth", 0) >= 0.85 and memory_router.record_beat(
        "depth_threshold",
        "convergence_ready",
        payload={"turns": player_state["turns_taken"]},
    ):
        beats_fired.append("depth_threshold:convergence_ready")
    return beats_fired


def _check_district_unlocks(
    target_agent: str, player_state: dict, beats_fired: list[str]
) -> tuple[dict, list[str]]:
    new_unlocks: list[str] = []
    already_unlocked = set(player_state.get("unlocked_districts") or [])
    for district_id in _LOCKABLE_DISTRICTS:
        if district_id in already_unlocked:
            continue
        try:
            result = unlock_engine.check_unlock(
                district_id=district_id,
                resonance=player_state["emotional_depth"],
                interactions=player_state["turns_taken"],
                emotional_tags=["warmth", "mystery"],
                veil_state=player_state.get("veil_state", "calm"),
                player_state=player_state,
            )
        except Exception:
            continue
        if result.unlocked:
            new_unlocks.append(district_id)
            player_state = memory_router.update_player_state(
                target_agent, unlock_district=district_id
            )
            memory_router.record_beat(
                "district_unlocked",
                district_id,
                payload={"resonance": player_state.get("emotional_depth")},
            )
            beats_fired.append(f"district_unlocked:{district_id}")
            log_event(
                {
                    "type": "district_unlocked",
                    "district": district_id,
                    "player_state": player_state,
                }
            )
    return player_state, new_unlocks


def _update_relationship(
    agent_id: str,
    target_agent: str,
    score: object,
    intent_info: dict | None,
) -> dict:
    try:
        cur_resistance = 70.0
        db = _ROOT / "03_memory" / "veil_town.sqlite"
        with sqlite3.connect(db) as conn:
            row = conn.execute(
                "SELECT resistance FROM relationships WHERE agent_a = ? AND agent_b = ?",
                (agent_id, target_agent),
            ).fetchone()
            if row:
                cur_resistance = float(row[0])
            else:
                init = persona_router.initial_state(agent_id)
                conn.execute(
                    """INSERT INTO relationships
                        (agent_a, agent_b, trust, affection, suspicion, resistance)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        agent_id,
                        target_agent,
                        init["trust"],
                        init["affection"],
                        init["suspicion"],
                        init["resistance"],
                    ),
                )
                cur_resistance = init["resistance"]

        raw_trust = score.emotional_depth * 2.0
        gate = persona_router.resistance_gate(agent_id, cur_resistance)
        effective_trust = raw_trust * gate if raw_trust >= 0 else raw_trust

        intent_label = (intent_info or {}).get("label", "unclear")
        intent_trust_bonus = {
            "deep": 2.0,
            "emotional": 2.5,
            "curious": 0.5,
            "challenging": 0.0,
            "unclear": 0.0,
            "shallow": -1.0,
            "hostile": -2.5,
        }.get(intent_label, 0.0)
        intent_aff_bonus = {
            "deep": 1.0,
            "emotional": 2.0,
            "shallow": -0.5,
            "hostile": -1.5,
        }.get(intent_label, 0.0)
        intent_susp_bonus = {
            "hostile": 4.0,
            "challenging": 1.0,
            "shallow": 0.5,
        }.get(intent_label, 0.0)

        return memory_router.update_relationship(
            agent_id,
            target_agent,
            trust_delta=effective_trust + intent_trust_bonus,
            affection_delta=score.prism_resonance * 1.0 + intent_aff_bonus,
            suspicion_delta=score.drift_risk * 3.0 + intent_susp_bonus,
        )
    except Exception as e:
        return {"error": str(e)}


def _send_agent_message(
    agent_id: str, target_agent: str, output: str
) -> tuple[str | None, str | None]:
    try:
        comms = agent_comms_mod.AgentComms(project_root=_ROOT)
        msg = comms.send(
            agent_id,
            target_agent,
            output,
            emotional_tone="warm-mysterious",
            canon_refs=_CANON_REFS,
        )
        return msg.msg_id, None
    except Exception as e:
        return None, str(e)


def _safe_asdict(obj):
    if obj is None:
        return None
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    if isinstance(obj, dict):
        return obj
    return str(obj)


def log_event(event: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {**event, "timestamp": datetime.now(UTC).isoformat()}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def run_once(
    agent_id: str = "mira",
    target_agent: str = "player",
    player_input: str | None = None,
) -> dict:
    """One full agent turn — scores, enforces canon, persists, fires events.

    If player_input is provided, it is written as a private memory under the
    player agent and used as the LLM's user_prompt so the agent responds in
    context instead of monologuing.
    """
    memory_router.init_db()

    intent_info = _capture_player_intent(player_input, target_agent)
    current_player_state = memory_router.read_player_state(target_agent)
    current_veil = current_player_state.get("veil_state", "calm")
    engine = event_engine_mod.EventEngine(project_root=_ROOT)

    user_prompt = _build_user_prompt(player_input)
    output, llm_meta, _preview_events = _generate_with_event_revision(
        agent_id, user_prompt, engine, current_player_state, intent_info
    )

    score, score_dict = _score_output(output, agent_id)
    canon_results, hard_violation, canon_error = _enforce_canon(output, agent_id)

    should_q, q_reason = quarantine.should_quarantine(
        score_dict, veil_state=current_veil
    )
    if hard_violation or should_q:
        event = _quarantine_event(
            agent_id=agent_id,
            output=output,
            llm_meta=llm_meta,
            score_dict=score_dict,
            current_veil=current_veil,
            hard_violation=hard_violation,
            should_q=should_q,
            q_reason=q_reason,
        )
        log_event(event)
        return event

    memory_id = memory_router.write_memory(
        "event",
        output,
        agent_id=agent_id,
        emotional_tags=["warmth", "mystery"],
        canon_refs=_CANON_REFS,
    )

    depth_delta = _depth_delta(score, intent_info)
    accumulated_depth = max(
        0.0, min(1.0, current_player_state["emotional_depth"] + depth_delta)
    )

    events_fired, events_error, dream, dream_alignment = _tick_events_and_dream(
        engine, agent_id, accumulated_depth
    )

    prior_veil = current_veil
    new_veil, veil_transition = _resolve_veil_state(prior_veil, accumulated_depth)

    dream_succeeded = dream is not None and not isinstance(dream, dict)
    player_state = memory_router.update_player_state(
        target_agent,
        depth_delta=depth_delta,
        dreams_seen_delta=1 if dream_succeeded else 0,
        veil_state=new_veil if veil_transition else None,
    )

    if veil_transition:
        memory_router.record_beat(
            "veil_transition", veil_transition, payload={"depth": accumulated_depth}
        )
        log_event(
            {
                "type": "veil_transition",
                "from": prior_veil,
                "to": new_veil,
                "depth": accumulated_depth,
            }
        )

    beats_fired = _record_narrative_beats(
        agent_id=agent_id,
        target_agent=target_agent,
        output=output,
        dream=dream,
        accumulated_depth=accumulated_depth,
        player_state=player_state,
    )
    player_state, new_unlocks = _check_district_unlocks(
        target_agent, player_state, beats_fired
    )

    relationship = _update_relationship(agent_id, target_agent, score, intent_info)
    msg_id, comms_error = _send_agent_message(agent_id, target_agent, output)
    voice_tags = _derive_voice_tags(score, intent_info, new_veil)

    event = {
        "agent": agent_id,
        "target": target_agent,
        "action": "run_once",
        "player_input": player_input,
        "output": output,
        "llm": llm_meta,
        "alignment": score_dict,
        "memory_id": memory_id,
        "player_state": player_state,
        "accumulated_depth": accumulated_depth,
        "new_unlocks": new_unlocks,
        "beats_fired": beats_fired,
        "veil_state": new_veil,
        "veil_transition": veil_transition,
        "image": _maybe_generate_image(agent_id, player_state, new_veil),
        "voice": _maybe_generate_voice(
            agent_id,
            output,
            new_veil,
            voice_tags,
            accumulated_depth,
        ),
        "intent": intent_info,
        "canon_results": [_safe_asdict(r) for r in canon_results],
        "canon_error": canon_error,
        "events_fired": [_safe_asdict(e) for e in events_fired],
        "events_error": events_error,
        "dream": _safe_asdict(dream),
        "dream_alignment": dream_alignment,
        "relationship": relationship,
        "msg_id": msg_id,
        "comms_error": comms_error,
    }
    log_event(event)
    return event


if __name__ == "__main__":
    print(json.dumps(run_once(), indent=2, default=str))
