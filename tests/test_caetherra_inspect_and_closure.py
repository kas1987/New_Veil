"""Tests for District 1 Inspect verb, dual-layer discovery, False Comfort, and Caetherra awakening."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
_API = ROOT / "04_runtime" / "game_api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from engine import (  # noqa: E402
    AdvanceVeil,
    ChooseBeat,
    Inspect,
    Talk,
    Travel,
    VeilGameEngine,
)


def _engine() -> VeilGameEngine:
    return VeilGameEngine(repo_root=ROOT, db_path=":memory:")


def test_zero_drift_dual_layer_inspect_and_absent_rule() -> None:
    engine = _engine()

    # Plaza starts at 350.0: mirror (<500) and lantern (<650) inspect on Prism surface with 0 drift & +0.0 resonance
    for _ in range(3):
        mirror_prism = engine.play(Inspect("mirror"))
        assert mirror_prism.ok is True
        assert "best" in mirror_prism.message.lower()
    stats = engine._row_dict("SELECT drift_count, resonance FROM player_stats WHERE player_id='player'")
    assert int(stats["drift_count"]) == 0
    assert float(stats["resonance"]) == 350.0
    assert "inspected:mirror:prism" in mirror_prism.scene["narrative_beats"]

    # Absent object not in location refuses cleanly; unknown object raises ValueError
    not_here = engine.play(Inspect("wall_of_the_unseen_gate"))
    assert not_here.ok is False
    with pytest.raises(ValueError):
        engine.play(Inspect("nonexistent_relic"))

    # At 500.0 Resonance, mirror reveals DQ layer (+5.0 once, 0 on repeat)
    engine._conn.execute("UPDATE player_stats SET resonance=500.0, has_crossed_first_threshold=1 WHERE player_id='player'")
    engine._conn.commit()
    mirror_dq = engine.play(Inspect("mirror"))
    assert mirror_dq.ok is True
    assert "+5.0 Resonance insight" in mirror_dq.message
    assert mirror_dq.scene["player"]["resonance"] == 505.0
    assert "inspected:mirror:dq" in mirror_dq.scene["narrative_beats"]

    repeat_dq = engine.play(Inspect("mirror"))
    assert repeat_dq.ok is True
    assert "+5.0 Resonance" not in repeat_dq.message
    assert repeat_dq.scene["player"]["resonance"] == 505.0

    # ABSENT_BELOW_THRESHOLD hides void_door below 750.0 even when at hollow_clearing
    engine._conn.execute("UPDATE player_stats SET resonance=749.0 WHERE player_id='player'")
    engine._conn.execute(
        "UPDATE world_state SET current_district='the_hollow', current_location='hollow_clearing', "
        "discovered_locations='[\"caetherra_plaza\", \"hollow_clearing\"]' WHERE player_id='player'"
    )
    engine._conn.commit()
    snap_low = engine.scene()
    assert not any(o["id"] == "void_door" for o in snap_low["objects_here"])
    assert engine.play(Inspect("void_door")).ok is False

    engine._conn.execute("UPDATE player_stats SET resonance=755.0 WHERE player_id='player'")
    engine._conn.commit()
    snap_high = engine.scene()
    assert any(o["id"] == "void_door" for o in snap_high["objects_here"])
    void_res = engine.play(Inspect("void_door"))
    assert void_res.ok is True
    assert void_res.scene["player"]["resonance"] == 760.0


def test_false_comfort_choice_and_full_caetherra_awakening_arc() -> None:
    engine = _engine()

    # Too early below 500.0
    too_early = engine.play(ChooseBeat("caetherra_false_comfort", "decline"))
    assert too_early.ok is False

    # Take 5 turns to satisfy Mira's Garden min_interactions >= 5, then cross 650.0
    for i in range(5):
        assert engine.play(Talk("mira", f"I wonder why warm lantern #{i} stays kind?")).ok is True
    engine._conn.execute("UPDATE player_stats SET resonance=655.0, has_crossed_first_threshold=1 WHERE player_id='player'")
    engine._conn.commit()

    # Accept then switch to decline (reversible False Comfort beat)
    accepted = engine.play(ChooseBeat("caetherra_false_comfort", "accept"))
    assert accepted.ok is True
    assert accepted.scene["district_status"]["false_comfort_state"] == "accepted"
    assert "false_comfort_accepted" in accepted.scene["narrative_beats"]

    declined = engine.play(ChooseBeat("caetherra_false_comfort", "decline"))
    assert declined.ok is True
    assert declined.scene["district_status"]["false_comfort_state"] == "declined"
    assert "false_comfort_declined" in declined.scene["narrative_beats"]
    assert "false_comfort_accepted" not in declined.scene["narrative_beats"]

    # Shift to storm, enter Listening Wall, inspect wall_of_the_unseen_gate at DQ depth
    engine.play(AdvanceVeil())
    engine.play(AdvanceVeil())
    assert engine.play(Travel("listening_wall")).ok is True
    gate = engine.play(Inspect("wall_of_the_unseen_gate"))
    assert gate.ok is True
    assert "+5.0 Resonance insight" in gate.message
    assert gate.scene["district_status"]["unseen_gate_discovered"] is True

    # Return to Plaza, enter Mira's Garden, speak with Mira -> caetherra_awakened fires
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("miras_garden")).ok is True
    garden_talk = engine.play(Talk("mira", "We saw the eastern gate together — what now?"))
    assert garden_talk.ok is True
    assert garden_talk.scene["district_status"]["caetherra_awakened"] is True
    assert "caetherra_awakened" in garden_talk.scene["narrative_beats"]

    # Save/load preserves narrative_beats and reset clears them
    assert engine.save("awakened_cp", "Caetherra Awakened").ok is True
    reset = engine.reset_session()
    assert reset.scene["narrative_beats"] == []
    assert reset.scene["district_status"]["caetherra_awakened"] is False

    loaded = engine.load("awakened_cp")
    assert loaded.scene["district_status"]["caetherra_awakened"] is True
    assert "inspected:wall_of_the_unseen_gate:dq" in loaded.scene["narrative_beats"]


def test_inspect_and_beat_choice_fastapi_contracts() -> None:
    server_mod = load_module("veil_game_server", ROOT / "04_runtime" / "game_api" / "server.py")
    client = TestClient(server_mod.create_app(db_path=":memory:"))

    inspect_resp = client.post("/api/world/inspect", json={"object_id": "lantern"})
    assert inspect_resp.status_code == 200
    body = inspect_resp.json()
    assert body["ok"] is True
    assert "inspected:lantern:prism" in body["state"]["narrative_beats"]

    assert client.post("/api/world/inspect", json={"object_id": "bogus_object"}).status_code == 404
    assert client.post("/api/world/beat-choice", json={"beat_id": "caetherra_false_comfort", "choice": "bad"}).status_code == 400


def test_dq_object_inspection_unlocks_integrative_synthesis_tokens() -> None:
    engine = _engine()
    # At starter 350.0, mirror DQ tokens are NOT yet unlocked
    assert "lingers" not in engine._revealed_tokens(350.0)

    # Raise above Mirror threshold (500.0) and inspect mirror at DQ depth
    engine._conn.execute(
        "UPDATE player_stats SET resonance=500.0, has_crossed_first_threshold=1 WHERE player_id='player'"
    )
    engine._conn.commit()
    inspected = engine.play(Inspect("mirror"))
    assert inspected.ok is True

    tokens = engine._revealed_tokens(505.0)
    assert "reflection" in tokens
    assert "lingers" in tokens

    # Speaking with interiority and open inquiry referencing the newly revealed mirror DQ token triggers Integrative Synthesis
    res = engine.play(
        Talk("mira", "I am afraid the reflection in this mirror lingers longer than warm comfort — why?")
    )
    assert res.ok is True and res.reply is not None
    assert res.reply.signals.get("integrativeSynthesis") is True
    assert res.reply.cue_type == "breakthrough_surge"
