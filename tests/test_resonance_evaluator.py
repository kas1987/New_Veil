"""Calibration & parity tests for the deterministic Resonance evaluator."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
RES_MOD = load_module("veil_resonance_evaluator", ROOT / "04_runtime" / "game_api" / "resonance_evaluator.py")

NPC_LINE = "The lanterns near the Listening Wall go out whenever the fog remembers who built them."


def _ctx(**overrides):
    defaults = dict(
        current_resonance=0.500,
        turns_taken=6,
        has_crossed_first_threshold=True,
        npc_last_line=NPC_LINE,
        recent_keywords=[],
        veil_state="calm",
    )
    defaults.update(overrides)
    return RES_MOD.TurnContext(**defaults)


def test_calibration_spectrum_matches_typescript_evaluator() -> None:
    # Command friction replaces the gain.
    r1 = RES_MOD.evaluate_talk_resonance("Open the gate.", _ctx())
    assert r1["delta"] == -0.030
    assert r1["new_resonance"] == 0.470
    assert r1["signals"]["frictionType"] == "command_or_dump_or_repeat"
    assert r1["cueType"] == "friction_damping"

    # A short echo of the NPC is still a question, not friction.
    r2 = RES_MOD.evaluate_talk_resonance("What wall?", _ctx())
    assert r2["delta"] == 0.035
    assert r2["new_resonance"] == 0.535
    assert r2["signals"]["mirroredNpc"] is True
    assert r2["signals"]["openInquiry"] is True

    # Listening: mirror, open question, a thematic word in a sentence, unhurried.
    r3 = RES_MOD.evaluate_talk_resonance(
        "Why do the lanterns go out when the fog rolls in?", _ctx()
    )
    assert r3["delta"] == 0.065
    assert r3["new_resonance"] == 0.565
    assert r3["signals"]["resonantWordsHit"] == ["why"]

    # Vulnerability plus a thematic word, capped together, plus the unhurried mark.
    r4 = RES_MOD.evaluate_talk_resonance(
        "I feel like I've seen those lanterns in a dream, and I'm afraid of what they remember.",
        _ctx(),
    )
    assert r4["delta"] == 0.070
    assert r4["new_resonance"] == 0.570
    assert r4["signals"]["vulnerableFraming"] is True
    assert r4["signals"]["resonantWordsHit"] == ["dream"]

    # A lexicon dump is friction. It does not farm the thematic mark.
    r5 = RES_MOD.evaluate_talk_resonance(
        "veil quasar prism truth memory shadow dream trust",
        _ctx(),
    )
    assert r5["delta"] == -0.030
    assert r5["signals"]["frictionType"] == "command_or_dump_or_repeat"
    assert r5["signals"]["resonantWordsHit"] == []


def test_grace_window_drift_and_suffocation_corruption() -> None:
    # Grace window holds 0.350 for first 5 talks before crossing 0.450
    g1 = RES_MOD.evaluate_talk_resonance(
        "Open the gate.",
        _ctx(current_resonance=0.350, turns_taken=1, has_crossed_first_threshold=False),
    )
    assert g1["new_resonance"] == 0.350
    assert g1["signals"]["graceFloorApplied"] is True
    assert g1["delta"] == 0.0

    # Drift every 3rd non-talk action (-0.010 calm, -0.020 storm)
    res, cnt, delta = RES_MOD.apply_drift(0.500, 2, "calm", in_grace_window=False)
    assert (res, cnt, delta) == (0.490, 0, -0.010)
    res_s, cnt_s, delta_s = RES_MOD.apply_drift(0.500, 2, "storm", in_grace_window=False)
    assert (res_s, cnt_s, delta_s) == (0.480, 0, -0.020)

    # Suffocation text corruption below 0.100
    assert "…" in RES_MOD.corrupt_suffocated_text("hello are you still listening")


def _encounter(stance: str, *, turns: int = 0, consecutive: int = 0, awarded: bool = False, tokens: list[str] | None = None) -> dict:
    return {
        "npcId": "npc_warden",
        "initialStance": stance if turns == 0 and consecutive == 0 else "hostile",
        "currentStance": stance,
        "turnsSpentInResistance": turns,
        "consecutiveAttunedTurns": consecutive,
        "breakthroughAwarded": awarded,
        "relevantUnlockedTokens": tokens or [],
    }


def test_hostile_reversal_pays_once_then_returns_to_the_turn_cap() -> None:
    """Same arc the client session eval runs: saving face, open, then one +0.150 bond."""
    resonance = 0.400
    encounter = _encounter("hostile")
    steps = [
        (
            "Leave this wall before the fog takes your voice.",
            "I am afraid the fog will take my voice near this wall — why?",
            "saved_face_stabilized",
            0.080,
            "guarded",
        ),
        (
            "I watched three visitors vanish into that mist.",
            "I remember feeling that same mist in a dream, how did they vanish?",
            "saturation_cap",
            0.080,
            "open",
        ),
        (
            "You actually listened instead of demanding answers.",
            "I don’t know the truth of this place yet, so I trust your answers — how did you endure?",
            "breakthrough_surge",
            0.150,
            "bonded",
        ),
    ]
    for npc_line, player_line, cue, delta, stance in steps:
        result = RES_MOD.evaluate_talk_resonance(
            player_line,
            _ctx(
                current_resonance=resonance,
                npc_last_line=npc_line,
                encounter=encounter,
            ),
        )
        assert result["cueType"] == cue
        assert result["delta"] == delta
        assert result["updatedEncounter"]["currentStance"] == stance
        resonance = result["new_resonance"]
        encounter = result["updatedEncounter"]
    assert resonance == 0.710

    capped = RES_MOD.evaluate_talk_resonance(
        "I feel safer knowing the lantern line still holds against the shadow — how long has it burned?",
        _ctx(
            current_resonance=resonance,
            npc_last_line="Stay close to the lantern line.",
            encounter=encounter,
        ),
    )
    assert capped["delta"] == 0.080
    assert capped["cueType"] == "saturation_cap"


def test_breakthrough_damps_to_0115_at_or_above_0800() -> None:
    result = RES_MOD.evaluate_talk_resonance(
        "I remember reading about the quasar fracture, and I am afraid of what happens when the prism opens.",
        _ctx(
            current_resonance=0.810,
            turns_taken=10,
            npc_last_line="The Dark Quasar only answers when the sky breaks.",
            encounter=_encounter("open", tokens=["quasar", "fracture"]),
        ),
    )
    assert result["cueType"] == "breakthrough_surge"
    assert result["delta"] == 0.115
    assert result["new_resonance"] == 0.925
    assert result["signals"]["integrativeSynthesis"] is True


def test_talk_caps_match_psychometric_attributes() -> None:
    import json

    talk = json.loads((ROOT / "14_psychometrics" / "attributes.json").read_text(encoding="utf-8"))["resonance_talk"]
    assert RES_MOD.TURN_CAP == talk["turn_cap"]
    assert RES_MOD.BREAKTHROUGH_BONUS == talk["breakthrough_bonus"]
    assert RES_MOD.BREAKTHROUGH_CEILING == talk["breakthrough_ceiling"]
    assert RES_MOD.HIGH_BAND_FROM == talk["high_band_from"]
    assert RES_MOD.HIGH_BAND_CEILING == talk["high_band_ceiling"]


def test_engine_talk_returns_signals_and_enforces_keyword_fatigue() -> None:
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    client = TestClient(server_mod.create_app(db_path=":memory:"))

    # First talk uses 'veil' -> fresh resonant word
    t1 = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "I wonder why the lanterns burn brighter behind the veil?"},
    ).json()
    assert t1["ok"] is True
    assert "signals" in t1
    assert "veil" in t1["signals"]["resonantWordsHit"]

    # Repeating the thematic word marks it fatigued and does not pay the thematic bonus again.
    t2 = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "veil"},
    ).json()
    assert t2["signals"]["fatiguedWords"] == ["veil"]
    assert t2["signals"]["resonantWordsHit"] == []
    assert t2["resonance_delta"] == 0.02
