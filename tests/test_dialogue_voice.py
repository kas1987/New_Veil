"""Tests for Caetherra authored beat packs, bounded memory recall, and voice selection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
_API = ROOT / "04_runtime" / "game_api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from engine import AdvanceVeil, Talk, Travel, VeilGameEngine  # noqa: E402

_VOICE = load_module("veil_dialogue_voice", _API / "dialogue_voice.py")
_EXPECTED_NPCS = ("mira", "solenne", "greeter", "witness", "threadwatcher")
_EXPECTED_BEATS = (
    "inspected:lantern:dq",
    "inspected:mirror:dq",
    "inspected:wall_of_the_unseen_gate:dq",
    "false_comfort_declined",
    "false_comfort_accepted",
    "caetherra_awakened",
)


def _engine() -> VeilGameEngine:
    return VeilGameEngine(repo_root=ROOT, db_path=":memory:")


def test_caetherra_beat_pack_complete_and_canon_compliant() -> None:
    pack = json.loads((ROOT / "13_agents" / "caetherra_dialogue_beats.json").read_text(encoding="utf-8"))
    npcs = pack["npcs"]
    assert set(npcs.keys()) == set(_EXPECTED_NPCS)

    for npc_id in _EXPECTED_NPCS:
        entry = npcs[npc_id]
        tiers = entry["tiers"]
        assert set(tiers.keys()) == {"stranger", "trusted", "deep"}
        for tier_name, families in tiers.items():
            assert set(families.keys()) == {"reflective", "grounded", "friction", "quasar"}
            for family_name, lines in families.items():
                assert len(lines) >= 2, f"{npc_id}.{tier_name}.{family_name} needs >= 2 lines"
                assert all(isinstance(line, str) and line.strip() for line in lines)
                if npc_id == "solenne":
                    for line in lines:
                        lower = line.lower()
                        assert "dark quasar" not in lower
                        assert "vael" not in lower
                if npc_id == "witness":
                    for line in lines:
                        assert len(line.split()) <= 8, f"Witness line too long: {line}"

        callbacks = entry["beat_callbacks"]
        assert set(callbacks.keys()) == set(_EXPECTED_BEATS)
        assert all(isinstance(v, str) and v.strip() for v in callbacks.values())


def test_bond_tier_and_stance_family_boundaries() -> None:
    assert _VOICE.bond_tier(0.0) == "stranger"
    assert _VOICE.bond_tier(34.9) == "stranger"
    assert _VOICE.bond_tier(35.0) == "trusted"
    assert _VOICE.bond_tier(74.9) == "trusted"
    assert _VOICE.bond_tier(75.0) == "deep"
    assert _VOICE.bond_tier(100.0) == "deep"

    assert _VOICE.stance_family("quasar_active", "standard_harmonic", {}, 1.0) == "quasar"
    assert _VOICE.stance_family("calm", "breakthrough_surge", {}, 6.0) == "quasar"
    assert _VOICE.stance_family("calm", "standard_harmonic", {"isDismissiveOrTransactional": True}, -1.2) == "friction"
    assert _VOICE.stance_family("calm", "standard_harmonic", {"openInquiry": True}, 1.5) == "reflective"
    assert _VOICE.stance_family("calm", "standard_harmonic", {}, 0.0) == "grounded"


def test_collect_bounded_memory_caps_history_and_gates_rumors_by_trusted_bond() -> None:
    engine = _engine()
    for i in range(7):
        engine._conn.execute(
            "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('shared', 'solenne', 'player', ?)",
            (f"solenne exchange {i}",),
        )
    engine._conn.execute(
        "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('shared', 'mira', 'player', ?)",
        ("Player: shared question | Mira: shared answer",),
    )
    engine._conn.execute(
        "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('private', 'mira', 'player', ?)",
        ("Player: quasar secret | Mira: private truth",),
    )
    engine._conn.execute(
        "INSERT INTO narrative_beats (player_id, beat_type, beat_label) VALUES ('player', 'inspect', 'inspected:lantern:dq')"
    )
    engine._conn.commit()

    untrusted = _VOICE.collect_bounded_memory(engine._conn, "solenne", {"mira": {"encounter": {"npcBond": 34.0}}})
    assert len(untrusted["private_exchanges"]) == 5
    assert untrusted["private_exchanges"] == [f"solenne exchange {i}" for i in range(2, 7)]
    assert untrusted["fired_beats"] == ["inspected:lantern:dq"]
    assert untrusted["earned_rumors"] == []

    trusted = _VOICE.collect_bounded_memory(engine._conn, "solenne", {"mira": {"encounter": {"npcBond": 35.0}}})
    assert len(trusted["earned_rumors"]) == 1
    assert trusted["earned_rumors"][0]["agent_id"] == "mira"
    assert "shared answer" in trusted["earned_rumors"][0]["content"]
    assert "private truth" not in trusted["earned_rumors"][0]["content"]


def test_engine_caetherra_npcs_distinct_voices_callbacks_and_rumors() -> None:
    engine = _engine()
    snap = engine.scene()
    mira = next(n for n in snap["npcs_here"] if n["id"] == "mira")
    assert mira["bond_tier"] == "stranger"

    # Non-repeating reflective turns for Mira
    r1 = engine.play(Talk("mira", "I wonder why the lanterns stay so warm beside the square?"))
    r2 = engine.play(Talk("mira", "I feel uneasy noticing how shadows fall near this archway — why?"))
    assert r1.ok and r2.ok and r1.reply and r2.reply
    assert r1.reply.text != r2.reply.text
    assert "warm Prism guidance" not in r1.reply.text

    # Greeter and Solenne keep distinct voices cleanly
    g1 = engine.play(Talk("greeter", "The lanterns look kind today — what draws travelers here?"))
    s1 = engine.play(Talk("solenne", "Do small candles keep burning when dusk settles here?"))
    assert g1.reply and s1.reply
    assert g1.reply.text != s1.reply.text
    assert "Prism" in g1.reply.text or "Congregation" in g1.reply.text or "Caetherra" in g1.reply.text or "lantern" in g1.reply.text.lower()

    # Fired beat callback triggers once on Mira, then resumes normal rotation
    engine._conn.execute(
        "INSERT INTO narrative_beats (player_id, beat_type, beat_label) VALUES ('player', 'inspect', 'inspected:lantern:dq')"
    )
    engine._conn.commit()
    cb_turn = engine.play(Talk("mira", "Look closely at the flame near my feet — what did you notice?"))
    assert cb_turn.reply is not None
    assert "shadow" in cb_turn.reply.text.lower()

    post_cb = engine.play(Talk("mira", "Walk with me beside the stone steps — why stay quiet?"))
    assert post_cb.reply is not None
    assert post_cb.reply.text != cb_turn.reply.text

    # Promote Mira to Trusted (>= 35) and confirm Solenne echoes earned rumor
    engine._conn.execute("UPDATE player_stats SET resonance=600.0, has_crossed_first_threshold=1 WHERE player_id='player'")
    engine._conn.execute(
        "INSERT INTO memories (scope, agent_id, subject_id, content) VALUES ('shared', 'mira', 'player', 'Player: asked gently | Mira: answered')"
    )
    arcs = json.loads(engine._row_dict("SELECT encounter_arcs FROM player_stats WHERE player_id='player'")["encounter_arcs"])
    arcs["npcs"]["mira"]["encounter"]["npcBond"] = 40.0
    arcs["npcs"]["solenne"]["encounter"]["npcBond"] = 40.0
    engine._conn.execute("UPDATE player_stats SET encounter_arcs=? WHERE player_id='player'", (json.dumps(arcs),))
    engine._conn.commit()

    # Solenne's first turn after a newly fired beat surfaces her beat callback once,
    # then the next reflective turn echoes Mira's Trusted shared rumor.
    sol_cb = engine.play(Talk("solenne", "Do you see how long the plaza flame reaches tonight?"))
    assert sol_cb.reply is not None
    assert "shadow" in sol_cb.reply.text.lower()

    rumor_turn = engine.play(Talk("solenne", "I feel steadier watching the dawn candles weave across the stone?"))
    assert rumor_turn.reply is not None
    assert "Mira" in rumor_turn.reply.text

    # Visit Listening Wall in storm for Witness and Threadwatcher distinct voices
    engine.play(AdvanceVeil())
    engine.play(AdvanceVeil())
    assert engine.play(Travel("listening_wall")).ok is True
    w_turn = engine.play(Talk("witness", "What happened beside the old mortar here?"))
    t_turn = engine.play(Talk("threadwatcher", "Why is that silver filament pulling across the wall?"))
    assert w_turn.reply and t_turn.reply
    assert len(w_turn.reply.text.split()) <= 10
    assert "?" in t_turn.reply.text


def test_live_llm_prompt_contract_and_fallback_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = _engine()
    engine._conn.execute(
        "INSERT INTO narrative_beats (player_id, beat_type, beat_label) VALUES ('player', 'inspect', 'inspected:mirror:dq')"
    )
    engine._conn.commit()

    captured: dict[str, str] = {}
    llm_mod = load_module("llm_provider", ROOT / "04_runtime" / "llm_provider.py")

    def fake_generate(agent_id: str, user_prompt: str | None = None, **kwargs):
        captured["agent_id"] = agent_id
        captured["user_prompt"] = user_prompt or ""
        return {
            "output": "You watched the warm lantern mirror closely, and Caetherra noticed.",
            "model": "qwen3:8b",
            "fallback": False,
        }

    monkeypatch.setenv("VEIL_USE_LIVE_LLM", "1")
    monkeypatch.setattr(llm_mod, "generate_agent_output", fake_generate)

    res = engine.play(Talk("mira", "Why did the plaza glass pause a half second?"))
    assert res.ok is True and res.reply is not None
    assert res.reply.text == "You watched the warm lantern mirror closely, and Caetherra noticed."
    assert captured["agent_id"] == "mira"
    assert "Bond: stranger" in captured["user_prompt"]
    assert "inspected:mirror:dq" in captured["user_prompt"]
    assert "Voice anchors" in captured["user_prompt"]

    # When Ollama returns fallback=True, engine cleanly falls back to authored beat pack instead of generic template
    monkeypatch.setattr(
        llm_mod,
        "generate_agent_output",
        lambda **kwargs: {"output": "generic placeholder", "model": "fallback", "fallback": True},
    )
    offline = engine.play(Talk("solenne", "I wonder why the warm candles linger here?"))
    assert offline.ok is True and offline.reply is not None
    assert offline.reply.text != "generic placeholder"
