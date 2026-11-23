"""Memory-aware per-NPC voice selection and live prompt formatting.

Implements ADR 0008's dialogue and bounded memory recall contract while leaving
resilience scoring strictly in ``resonance_evaluator.py``.
"""

from __future__ import annotations

import sqlite3
from typing import Any


def bond_tier(npc_bond: float) -> str:
    """Map numeric NPC Bond (0-100) into qualitative relationship bands."""
    if npc_bond < 35.0:
        return "stranger"
    if npc_bond < 75.0:
        return "trusted"
    return "deep"


def stance_family(
    veil_state: str,
    cue_type: str,
    signals: dict[str, Any],
    delta: float,
) -> str:
    """Collapse fine-grained encounter state into 4 authored stance families."""
    if veil_state == "quasar_active" or cue_type == "breakthrough_surge":
        return "quasar"
    if signals.get("isDismissiveOrTransactional") or delta < 0.0:
        return "friction"
    if delta > 0.0 and (
        signals.get("mirroredNpc")
        or signals.get("openInquiry")
        or signals.get("vulnerableFraming")
        or signals.get("resonantWordsHit")
    ):
        return "reflective"
    return "grounded"


def collect_bounded_memory(
    conn: sqlite3.Connection,
    npc_id: str,
    npc_arcs: dict[str, Any],
) -> dict[str, Any]:
    """Read bounded private history, world beats, and Trusted earned rumors."""
    priv_rows = conn.execute(
        "SELECT scope, content FROM memories "
        "WHERE agent_id=? AND scope IN ('shared', 'private') "
        "ORDER BY id DESC LIMIT 5",
        (npc_id,),
    ).fetchall()
    private_exchanges = [str(r["content"]) for r in reversed(priv_rows)]

    beat_rows = conn.execute(
        "SELECT beat_label FROM narrative_beats "
        "WHERE player_id='player' ORDER BY id ASC"
    ).fetchall()
    fired_beats = [str(r["beat_label"]) for r in beat_rows]

    trusted_sources = {
        aid
        for aid, entry in npc_arcs.items()
        if aid != npc_id
        and float(((entry or {}).get("encounter") or {}).get("npcBond", 0.0)) >= 35.0
    }

    earned_rumors: list[dict[str, str]] = []
    if trusted_sources:
        placeholders = ",".join("?" for _ in trusted_sources)
        rumor_rows = conn.execute(
            f"SELECT agent_id, content FROM memories "
            f"WHERE scope='shared' AND subject_id='player' AND agent_id IN ({placeholders}) "
            f"ORDER BY id DESC LIMIT 3",
            tuple(sorted(trusted_sources)),
        ).fetchall()
        for r in reversed(rumor_rows):
            earned_rumors.append(
                {"agent_id": str(r["agent_id"]), "content": str(r["content"])}
            )

    return {
        "private_exchanges": private_exchanges,
        "fired_beats": fired_beats,
        "earned_rumors": earned_rumors,
    }


def _pick_non_repeating(lines: list[str], index_seed: int, last_line: str) -> str:
    if not lines:
        return ""
    chosen = lines[index_seed % len(lines)]
    if chosen == last_line and len(lines) > 1:
        chosen = lines[(index_seed + 1) % len(lines)]
    return chosen


def select_offline_reply(
    beats_pack: dict[str, Any],
    npc_id: str,
    char: dict[str, Any],
    characters: dict[str, dict[str, Any]],
    resonance: float,
    veil_state: str,
    cue_type: str,
    signals: dict[str, Any],
    delta: float,
    npc_bond: float,
    interactions: int,
    last_npc_line: str,
    memory_ctx: dict[str, Any],
    player_text: str,
) -> str:
    """Select an authored beat line (or generic fallback for non-Caetherra NPCs)."""
    if resonance < 100.0:
        return "..."

    npc_pack = (beats_pack.get("npcs") or {}).get(npc_id)
    if npc_pack:
        callbacks = npc_pack.get("beat_callbacks") or {}
        private_text = "\n".join(memory_ctx.get("private_exchanges") or [])
        for beat in reversed(memory_ctx.get("fired_beats") or []):
            cb_line = callbacks.get(beat)
            if cb_line and cb_line != last_npc_line and cb_line not in private_text:
                return str(cb_line)

        tier = bond_tier(npc_bond)
        family = stance_family(veil_state, cue_type, signals, delta)
        if resonance < 350.0 and family != "quasar":
            family = "friction"

        tier_map = (npc_pack.get("tiers") or {}).get(tier) or {}
        lines = list(tier_map.get(family) or tier_map.get("grounded") or [])
        base_line = _pick_non_repeating(lines, max(0, interactions), last_npc_line)
        if not base_line:
            base_line = f"{char['display_name']} answers warmly: \"{char['greeting']}\""

        rumors = [
            r
            for r in (memory_ctx.get("earned_rumors") or [])
            if r.get("agent_id") in ("mira", "solenne", "greeter", "threadwatcher")
        ]
        rumor_prefix = str(npc_pack.get("rumor_prefix") or "").strip()
        if (
            rumors
            and rumor_prefix
            and npc_id != "witness"
            and tier in ("trusted", "deep")
            and family == "reflective"
        ):
            src_id = rumors[-1]["agent_id"]
            src_name = (characters.get(src_id) or {}).get("display_name") or src_id.title()
            rendered_prefix = rumor_prefix.format(source=src_name)
            if rendered_prefix not in last_npc_line and rendered_prefix not in private_text:
                return f"{rendered_prefix} {base_line}"
        return base_line

    # Non-Caetherra fallback (retains pre-existing district behavior until authored)
    depth_hits = len(signals.get("resonantWordsHit") or [])
    if resonance < 350.0:
        return (
            f"{char['display_name']} looks past you, answering briefly: "
            '"Not now. The streets are quieter than they seem."'
        )
    if veil_state == "quasar_active":
        return (
            f"{char['display_name']} studies you beneath the Quasar's gravity. "
            f"\"You asked about '{player_text[:60]}'. Strip away the Prism's comfort—"
            f"{char['hidden_function'].lower()}.\""
        )
    if depth_hits >= 1 or signals.get("vulnerableFraming") or resonance >= 550.0:
        return (
            f"{char['display_name']} pauses, the surface smile softening into real attention. "
            f"\"Few travelers look past the warmth so quickly. Remember: {char['surface_function']}. "
            'Keep listening, and the Veil will answer."'
        )
    return f"{char['display_name']} answers warmly: \"{char['greeting']}\""


def build_live_llm_prompt(
    beats_pack: dict[str, Any],
    npc_id: str,
    location_name: str,
    veil_state: str,
    resonance: float,
    npc_bond: float,
    stance: str,
    cue_type: str,
    memory_ctx: dict[str, Any],
    player_text: str,
) -> str:
    """Format a bounded, stance- and beat-anchored prompt for local Ollama."""
    tier = bond_tier(npc_bond)
    npc_pack = (beats_pack.get("npcs") or {}).get(npc_id) or {}
    tier_map = (npc_pack.get("tiers") or {}).get(tier) or {}
    anchors: list[str] = []
    for key in ("reflective", "grounded", "quasar"):
        lines = tier_map.get(key) or []
        if lines:
            anchors.append(str(lines[0]))
        if len(anchors) >= 2:
            break

    parts = [
        (
            f"[Location: {location_name} | Veil: {veil_state} | Resonance: {resonance:.1f}/1000 | "
            f"Bond: {tier} ({npc_bond:.1f}/100) | Stance: {stance} | Cue: {cue_type}]"
        )
    ]
    if anchors:
        parts.append("Voice anchors (match cadence, do not copy verbatim):\n- " + "\n- ".join(anchors))
    private_exchanges = memory_ctx.get("private_exchanges") or []
    if private_exchanges:
        parts.append("Recent exchanges with this visitor:\n- " + "\n- ".join(private_exchanges[-5:]))
    fired_beats = memory_ctx.get("fired_beats") or []
    if fired_beats:
        parts.append("World beats observed: " + ", ".join(fired_beats))
    rumors = memory_ctx.get("earned_rumors") or []
    if rumors:
        parts.append(
            "Earned rumors from trusted residents:\n- "
            + "\n- ".join(f"{r['agent_id']}: {r['content'][:140]}" for r in rumors)
        )
    parts.append(f"Player says: {player_text}\nRespond in voice in 1-4 concise sentences.")
    return "\n\n".join(parts)
