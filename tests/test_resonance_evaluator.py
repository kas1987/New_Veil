"""Calibration & parity tests for the deterministic 3-layer 0-1000 Resonance evaluator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
RES_MOD = load_module("veil_resonance_evaluator", ROOT / "04_runtime" / "game_api" / "resonance_evaluator.py")
CORPUS_PATH = ROOT / "14_psychometrics" / "calibration_corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))

NPC_LINE = "The lanterns near the Listening Wall go out whenever the fog remembers who built them."


def _ctx(**overrides):
    defaults = {
        "current_resonance": 500.0,
        "turns_taken": 6,
        "has_crossed_first_threshold": True,
        "npc_last_line": NPC_LINE,
        "recent_keywords": [],
        "veil_state": "calm",
    }
    defaults.update(overrides)
    return RES_MOD.TurnContext(**defaults)


def test_calibration_spectrum_matches_typescript_evaluator() -> None:
    # Command friction replaces the gain.
    r1 = RES_MOD.evaluate_talk_resonance("Open the gate.", _ctx())
    assert r1["delta"] == -1.2
    assert r1["new_resonance"] == 498.8
    assert r1["signals"]["frictionType"] == "command_or_dump_or_repeat"
    assert r1["cueType"] == "friction_damping"

    # A short echo of the NPC is still a question, not friction.
    r2 = RES_MOD.evaluate_talk_resonance("What wall?", _ctx())
    assert r2["delta"] == 1.1
    assert r2["new_resonance"] == 501.1
    assert r2["signals"]["mirroredNpc"] is True
    assert r2["signals"]["openInquiry"] is True

    # Listening: mirror, open question, a thematic word in a sentence, unhurried.
    r3 = RES_MOD.evaluate_talk_resonance(
        "Why do the lanterns go out when the fog rolls in?", _ctx()
    )
    assert r3["delta"] == 2.0
    assert r3["new_resonance"] == 502.0
    assert r3["signals"]["resonantWordsHit"] == ["why"]

    # Vulnerability plus a thematic word, capped together, plus the unhurried mark.
    r4 = RES_MOD.evaluate_talk_resonance(
        "I feel like I've seen those lanterns in a dream, and I'm afraid of what they remember.",
        _ctx(),
    )
    assert r4["delta"] == 2.1
    assert r4["new_resonance"] == 502.1
    assert r4["signals"]["vulnerableFraming"] is True
    assert r4["signals"]["resonantWordsHit"] == ["dream"]

    # A lexicon dump is friction. It does not farm the thematic mark.
    r5 = RES_MOD.evaluate_talk_resonance(
        "veil quasar prism truth memory shadow dream trust",
        _ctx(),
    )
    assert r5["delta"] == -1.2
    assert r5["signals"]["frictionType"] == "command_or_dump_or_repeat"
    assert r5["signals"]["resonantWordsHit"] == []


@pytest.mark.parametrize("probe", CORPUS["single_turn_probes"], ids=lambda p: p["id"])
def test_shared_calibration_corpus_probes(probe: dict) -> None:
    """Guarantee exact parity with calibration_corpus.json across all single-turn probes."""
    raw_ctx = probe["ctx"]
    ctx = RES_MOD.TurnContext(
        current_resonance=float(raw_ctx["currentResonance"]),
        turns_taken=int(raw_ctx["turnsTaken"]),
        has_crossed_first_threshold=bool(raw_ctx["hasCrossedFirstThreshold"]),
        npc_last_line=str(raw_ctx["npcLastLine"]),
        recent_keywords=list(raw_ctx.get("recentKeywords") or []),
        veil_state=str(raw_ctx.get("veilState") or "calm"),
        player_last_line=str(raw_ctx.get("playerLastLine") or ""),
        encounter=raw_ctx.get("encounter"),
        personality_weights=raw_ctx.get("personalityWeights"),
    )
    res = RES_MOD.evaluate_talk_resonance(probe["playerLine"], ctx)
    exp = probe["expected"]

    if "delta" in exp:
        assert res["delta"] == exp["delta"]
    if "newResonance" in exp:
        assert res["new_resonance"] == exp["newResonance"]
    if "cueType" in exp:
        assert res["cueType"] == exp["cueType"]
    if "stance" in exp:
        assert res["updatedEncounter"]["currentStance"] == exp["stance"]
    for signal_key in (
        "frictionType",
        "mirroredNpc",
        "openInquiry",
        "interiority",
        "thematicInSentence",
        "sustainedCadence",
        "resonantWordsHit",
        "graceFloorApplied",
        "hitSaturationCap",
        "trustRupture",
        "quasarAmplified",
        "integrativeSynthesis",
        "npcTaperApplied",
        "npcBond",
    ):
        if signal_key in exp:
            assert res["signals"][signal_key] == exp[signal_key]


def test_psychometric_eval_runner_all_archetypes_pass() -> None:
    if str(ROOT / "14_psychometrics") not in sys.path:
        sys.path.insert(0, str(ROOT / "14_psychometrics"))
    eval_runner = load_module("veil_eval_runner", ROOT / "14_psychometrics" / "eval_runner.py")
    results = [eval_runner.run_archetype(script) for script in CORPUS["archetype_scripts"]]
    assert len(results) == 7
    for r in results:
        assert r["passed"], f"Archetype {r['id']} failed: {r['failures']}"
        assert not r["exploit_flags"], f"Archetype {r['id']} flagged exploit: {r['exploit_flags']}"


def test_grace_window_drift_and_suffocation_corruption() -> None:
    # Grace window holds 350.0 for first 5 talks before crossing 450.0
    g1 = RES_MOD.evaluate_talk_resonance(
        "Open the gate.",
        _ctx(current_resonance=350.0, turns_taken=1, has_crossed_first_threshold=False),
    )
    assert g1["new_resonance"] == 350.0
    assert g1["signals"]["graceFloorApplied"] is True
    assert g1["delta"] == 0.0

    # Drift every 3rd non-talk action (-0.5 calm, -1.0 storm)
    res, cnt, delta = RES_MOD.apply_drift(500.0, 2, "calm", in_grace_window=False)
    assert (res, cnt, delta) == (499.5, 0, -0.5)
    res_s, cnt_s, delta_s = RES_MOD.apply_drift(500.0, 2, "storm", in_grace_window=False)
    assert (res_s, cnt_s, delta_s) == (499.0, 0, -1.0)

    # Suffocation text corruption below 100.0
    assert "…" in RES_MOD.corrupt_suffocated_text("hello are you still listening")


def _encounter(
    stance: str,
    *,
    turns: int = 0,
    consecutive: int = 0,
    awarded: bool = False,
    tokens: list[str] | None = None,
    bond: float = 0.0,
    contrib: float = 0.0,
) -> dict:
    return {
        "npcId": "npc_warden",
        "initialStance": stance if turns == 0 and consecutive == 0 else "hostile",
        "currentStance": stance,
        "turnsSpentInResistance": turns,
        "consecutiveAttunedTurns": consecutive,
        "breakthroughAwarded": awarded,
        "relevantUnlockedTokens": tokens or [],
        "npcBond": bond,
        "townContribution": contrib,
    }


def test_hostile_reversal_pays_once_then_returns_to_the_turn_cap() -> None:
    """Same arc the client session eval runs: saving face, open, then one +6.0 bond."""
    resonance = 400.0
    encounter = _encounter("hostile")
    steps = [
        (
            "Leave this wall before the fog takes your voice.",
            "I am afraid the fog will take my voice near this wall — why?",
            "saved_face_stabilized",
            2.5,
            "guarded",
        ),
        (
            "I watched three visitors vanish into that mist.",
            "I remember feeling that same mist in a dream, how did they vanish?",
            "saturation_cap",
            2.5,
            "open",
        ),
        (
            "You actually listened instead of demanding answers.",
            "I don’t know the truth of this place yet, so I trust your answers — how did you endure?",
            "breakthrough_surge",
            6.0,
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
    assert resonance == 411.0

    capped = RES_MOD.evaluate_talk_resonance(
        "I feel safer knowing the lantern line still holds against the shadow — how long has it burned?",
        _ctx(
            current_resonance=resonance,
            npc_last_line="Stay close to the lantern line.",
            encounter=encounter,
        ),
    )
    assert capped["delta"] == 2.5
    assert capped["cueType"] == "saturation_cap"


def test_breakthrough_damps_to_4_0_at_or_above_800_0() -> None:
    result = RES_MOD.evaluate_talk_resonance(
        "I remember reading about the quasar fracture, and I am afraid of what happens when the prism opens.",
        _ctx(
            current_resonance=810.0,
            turns_taken=10,
            npc_last_line="The Dark Quasar only answers when the sky breaks.",
            encounter=_encounter("open", tokens=["quasar", "fracture"]),
        ),
    )
    assert result["cueType"] == "breakthrough_surge"
    assert result["delta"] == 4.0
    assert result["new_resonance"] == 814.0
    assert result["signals"]["integrativeSynthesis"] is True


def test_talk_caps_match_psychometric_attributes() -> None:
    attrs = json.loads((ROOT / "14_psychometrics" / "attributes.json").read_text(encoding="utf-8"))
    talk = attrs["resonance_talk"]
    bond_cfg = attrs["npc_bond"]
    assert RES_MOD.TURN_CAP == talk["turn_cap"]
    assert RES_MOD.BREAKTHROUGH_BONUS == talk["breakthrough_bonus"]
    assert RES_MOD.BREAKTHROUGH_CEILING == talk["breakthrough_ceiling"]
    assert RES_MOD.HIGH_BAND_FROM == talk["high_band_from"]
    assert RES_MOD.HIGH_BAND_CEILING == talk["high_band_ceiling"]
    assert RES_MOD.NPC_CONTRIBUTION_SOFT_CAP == bond_cfg["soft_cap_town_contribution"]
    assert RES_MOD.NPC_TAPER_MULTIPLIER == bond_cfg["taper_multiplier"]


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

    # Repeating 'veil' marks it fatigued; mirrors Mira's previous reply (0.6 * 1.1 mirror weight = 0.66).
    t2 = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "veil"},
    ).json()
    assert t2["signals"]["fatiguedWords"] == ["veil"]
    assert t2["signals"]["resonantWordsHit"] == []
    assert t2["resonance_delta"] == 0.66


def test_negative_dynamics_rupture_quasar_amplification_and_synthesis_fix() -> None:
    # 1. Long hostile dismissal overrides mirror/interiority/cadence -> -1.8
    hostile = RES_MOD.evaluate_talk_resonance(
        "I honestly don't care about your silly lanterns anymore.",
        _ctx(
            current_resonance=500.0,
            npc_last_line="The lanterns burn gently along the plaza.",
            encounter=_encounter("guarded"),
        ),
    )
    assert hostile["delta"] == -1.8
    assert hostile["signals"]["frictionType"] == "hostile_dismissal"
    assert hostile["updatedEncounter"]["currentStance"] == "hostile"

    # 2. Trust Rupture on bonded NPC -> -3.0 and bonded -> guarded
    bonded_enc = _encounter("bonded", turns=2, consecutive=3)
    rupture = RES_MOD.evaluate_talk_resonance(
        "Shut up, this is a waste of time.",
        _ctx(current_resonance=650.0, encounter=bonded_enc),
    )
    assert rupture["cueType"] == "trust_rupture"
    assert rupture["signals"]["trustRupture"] is True
    assert rupture["delta"] == -3.0
    assert rupture["updatedEncounter"]["currentStance"] == "guarded"

    # 3. Canon #15: Quasar active amplifies negative by 1.25x (-3.0 -> -3.75)
    q_rupture = RES_MOD.evaluate_talk_resonance(
        "Shut up, you are lying.",
        _ctx(current_resonance=650.0, veil_state="quasar_active", encounter=_encounter("bonded", turns=2, consecutive=3)),
    )
    assert q_rupture["signals"]["quasarAmplified"] is True
    assert q_rupture["delta"] == -3.75

    # 4. Two consecutive standard friction turns cool open -> guarded
    e1 = RES_MOD.evaluate_talk_resonance("ok", _ctx(encounter=_encounter("open", turns=1, consecutive=2)))
    assert e1["updatedEncounter"]["currentStance"] == "open"
    e2 = RES_MOD.evaluate_talk_resonance("yeah", _ctx(encounter=e1["updatedEncounter"]))
    assert e2["updatedEncounter"]["currentStance"] == "guarded"
    assert e2["signals"]["stanceTransition"] == "open -> guarded"

    # 5. Synthesis leak fixed: starter 350.0 player does NOT get generic 'veil' token;
    #    suffocation < 100.0 loops travel back to caetherra_plaza; reset restores 350.0.
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    client = TestClient(server_mod.create_app(db_path=":memory:"))
    engine = client.app.state.engine
    assert "veil" not in engine._revealed_tokens(350.0)

    # First interiority turn mentioning 'veil' does NOT fire +3.5 breakthrough surge
    t1 = client.post(
        "/api/dialogue/turn",
        json={"npc_id": "mira", "message": "I wonder why the lanterns burn behind the veil here?"},
    ).json()
    assert t1["signals"]["integrativeSynthesis"] is False
    assert t1["resonance_delta"] <= 2.5

    # Suffocation < 100.0 loops road back to caetherra_plaza
    engine._conn.execute("UPDATE player_stats SET resonance = 50.0 WHERE player_id='player'")
    engine._conn.commit()
    loop_resp = client.post("/api/world/travel", json={"location_id": "solstice_bazaar"}).json()
    assert loop_resp["ok"] is False
    assert "Caetherra Plaza" in loop_resp["message"]
    assert loop_resp["state"]["world"]["current_location"]["id"] == "caetherra_plaza"

    # Reset restores 350.0 session
    reset_resp = client.post("/api/game/reset").json()
    assert reset_resp["ok"] is True
    assert reset_resp["state"]["player"]["resonance"] == 350.0
