"""Session behavior of VeilGameEngine, crossed at scene/play."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_API = ROOT / "04_runtime" / "game_api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from engine import (  # noqa: E402
    AdvanceVeil,
    Buy,
    Resolve,
    Talk,
    ToggleParty,
    Travel,
    Use,
    VeilGameEngine,
)

_DEEP = "I feel like the lanterns here remember something honest — why does the town stay so warm?"
_REFLECTIVE_LINES = (
    "I feel like the lanterns here remember something honest — why does the town stay so warm?",
    "I wonder what lies beneath the surface warmth when someone truly listens to this place?",
    "I am afraid I might miss what you are quietly testing — how do travelers earn real trust?",
    "Honestly, I remember feeling lost before arriving; what does this shelter ask of us?",
    "I don't know if I am ready for the deeper weight, yet I want to stay and listen closely?",
    "I hope my questions are not hollow — tell me about the quiet harbor you keep here?",
)


def _engine() -> VeilGameEngine:
    return VeilGameEngine(repo_root=ROOT, db_path=":memory:")


def _talk(engine: VeilGameEngine, npc_id: str = "mira", text: str = _DEEP):
    return engine.play(Talk(npc_id, text))


def _raise_resonance(engine: VeilGameEngine, target: float) -> None:
    """Verify reflective talk builds Resonance cleanly, then advance to high-band target."""
    for idx in range(6):
        result = _talk(engine, text=_REFLECTIVE_LINES[idx % len(_REFLECTIVE_LINES)])
        assert result.ok is True
    cur = float(engine.scene()["player"]["resonance"])
    if cur < target:
        engine._conn.execute(
            "UPDATE player_stats SET resonance=?, has_crossed_first_threshold=1 WHERE player_id='player'",
            (target,),
        )
        engine._conn.commit()
    assert engine.scene()["player"]["resonance"] >= target


def test_single_npc_grinding_builds_personal_bond_but_tapers_town_resonance() -> None:
    engine = _engine()
    start_res = engine.scene()["player"]["resonance"]
    prompts = (
        "I feel uncertain about wall mirror #{i} in this warm harbor — how does the town answer?",
        "I remember feeling lost beside mirror #{i} in this warm harbor — why does patience stay?",
        "I wonder whether trusting this warm harbor mirror #{i} reveals a deeper memory?",
    )
    for idx in range(26):
        res = _talk(engine, npc_id="mira", text=prompts[idx % len(prompts)].format(i=idx))
        assert res.ok is True
    snap = engine.scene()
    mira = next(n for n in snap["npcs_here"] if n["id"] == "mira")
    assert mira["bond"] >= 95.0
    assert snap["player"]["resonance"] > start_res + 50.0
    assert snap["player"]["resonance"] < 425.0  # Tapered well below 500.0 Ashveil gate


def test_locked_district_and_missing_road_leave_the_scene_unchanged() -> None:
    engine = _engine()
    no_road = engine.play(Travel("hollow_clearing"))
    assert no_road.ok is False
    assert "No direct road" in no_road.message
    assert no_road.scene["world"]["current_location"]["id"] == "caetherra_plaza"

    locked = engine.play(Travel("ashveil_forges"))
    assert locked.ok is False
    assert "Resonance" in locked.message
    assert locked.scene["world"]["current_location"]["id"] == "caetherra_plaza"


def test_quasar_reveals_true_name_and_weighs_on_the_bond() -> None:
    engine = _engine()
    _raise_resonance(engine, 805.0)
    for expected in ("still", "storm", "quasar_active"):
        shifted = engine.play(AdvanceVeil())
        assert shifted.scene["world"]["veil_state"] == expected

    mira = next(n for n in engine.scene()["npcs_here"] if n["id"] == "mira")
    assert "Thesmera Locke" in mira["display_name"]
    before_suspicion = mira["relationship"]["suspicion"]
    before_affection = mira["relationship"]["affection"]

    after = _talk(engine, text="I am ready to face the Dark Quasar truth.")
    mira_after = next(n for n in after.scene["npcs_here"] if n["id"] == "mira")
    assert mira_after["relationship"]["suspicion"] > before_suspicion
    assert mira_after["relationship"]["affection"] < before_affection


def test_seeded_encounter_is_one_shot_and_save_restores_the_plaza() -> None:
    engine = _engine()
    baseline = engine.save("baseline", "Day 1 Start")
    assert baseline.ok is True
    assert baseline.message == "Day 1 Start"

    fought = engine.play(Resolve("trial_prism_surface", "accept_warmth", seed=0))
    assert fought.ok is True
    assert fought.check is not None
    assert fought.check.success is True
    assert fought.check.roll == 13
    assert fought.scene["player"]["xp"] > 0

    again = engine.play(Resolve("trial_prism_surface", "accept_warmth", seed=0))
    assert again.ok is False
    assert again.check is None

    engine.play(Travel("solstice_bazaar"))
    loaded = engine.load("baseline")
    assert loaded.ok is True
    assert loaded.scene["world"]["current_location"]["id"] == "caetherra_plaza"
    assert loaded.scene["player"]["xp"] == 0


def test_save_restores_a_bond_and_a_faction_the_player_then_earns() -> None:
    engine = _engine()
    engine.play(Travel("solstice_bazaar"))
    snapshot = engine.save("before_kaelen", "Before the lanternwright")
    assert snapshot.scene["player"]["turns_taken"] >= 0

    talked = _talk(engine, "kaelen_lanternwright")
    assert talked.ok is True
    guild = next(f for f in talked.scene["factions"] if f["id"] == "lantern_guild")
    assert guild["reputation"] == 15

    loaded = engine.load("before_kaelen")
    mira = next(n for n in loaded.scene["npcs_here"] if n["id"] == "kaelen_lanternwright")
    guild_again = next(f for f in loaded.scene["factions"] if f["id"] == "lantern_guild")
    assert mira["relationship"]["interactions"] == 0
    assert guild_again["reputation"] == 0


def test_a_key_item_survives_use() -> None:
    engine = _engine()
    assert engine.play(Resolve("trial_prism_surface", "accept_warmth", seed=0)).ok is True
    assert engine.play(Travel("solstice_bazaar")).ok is True
    assert _talk(engine, "kaelen_lanternwright").ok is True
    _raise_resonance(engine, 500.0)
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("ashveil_forges")).ok is True
    bought = engine.play(Buy("key"))
    assert bought.ok is True, bought.message
    used = engine.play(Use("key"))
    assert used.ok is False
    assert any(item["id"] == "key" for item in used.scene["inventory"])


def test_played_path_reaches_the_true_ending() -> None:
    engine = _engine()
    assert engine.scene()["ending_status"]["trajectory"] == "false_ending_risk"

    _raise_resonance(engine, 820.0)
    assert engine.scene()["player"]["turns_taken"] >= 6
    fought = engine.play(Resolve("trial_prism_surface", "pierce_illusion", seed=0))
    assert fought.ok is True

    engine.play(Travel("solstice_bazaar"))
    lantern = engine.play(Buy("lantern"))
    assert lantern.ok is True, lantern.message
    assert engine.play(Travel("caetherra_plaza")).ok is True
    assert engine.play(Travel("stillward_cloister")).ok is True, engine.scene()["world"]["current_location"]["id"]
    assert engine.play(Travel("hollow_clearing")).ok is True
    assert engine.play(Travel("gravity_spire_deck")).ok is True
    for _ in range(3):
        engine.play(AdvanceVeil())
    assert engine.scene()["world"]["veil_state"] == "quasar_active"
    opened = engine.play(Travel("void_threshold"))
    assert opened.ok is True, opened.message

    ending = engine.scene()["ending_status"]
    assert ending["trajectory"] == "true_ending_ready"
    assert all(ending["criteria"].values())
    assert "void_threshold" in ending["hidden_paths_found"]


def test_party_codex_portrait_and_status_stay_off_the_session_verbs() -> None:
    engine = _engine()
    added = engine.play(ToggleParty("solenne"))
    assert added.ok is True
    assert "solenne" in added.scene["world"]["active_party"]
    dismissed = engine.play(ToggleParty("mira"))
    assert "mira" not in dismissed.scene["world"]["active_party"]
    refused = engine.play(ToggleParty("greeter"))
    assert refused.ok is False

    entries = engine.codex()
    lore = next(entry for entry in entries if entry["id"] == "lore_bible")
    quasar = next(entry for entry in entries if entry["id"] == "dark_quasar")
    assert lore["unlocked"] is True
    assert quasar["unlocked"] is False

    bound = engine.bind_portrait("mira", "adeline")
    mira = next(n for n in bound.scene["npcs_here"] if n["id"] == "mira")
    assert mira["portrait_url"] == "/api/media/portrait/adeline"

    report = engine.status(shelf_count=3)
    assert "live_llm_enabled" in report
    assert report["local_shelf_characters"] == 3


def test_resolve_populates_message_and_save_restores_resonance_metadata() -> None:
    engine = _engine()
    fought = engine.play(Resolve("trial_prism_surface", "accept_warmth", seed=0))
    assert fought.ok is True
    assert fought.check is not None
    assert fought.message == fought.check.outcome_text

    # Talk with 'veil', build drift_count, and save
    _talk(engine, text="I wonder what hides behind the veil when lanterns burn bright?")
    engine.play(Travel("solstice_bazaar"))
    saved = engine.save("meta_check", "Metadata Snapshot")
    assert saved.ok is True

    # Mutate metadata after save via more dialogue and travel
    _talk(engine, "kaelen_lanternwright", "Why do shadows gather near the mirror?")
    engine._conn.execute(
        "UPDATE player_stats SET has_crossed_first_threshold=1, drift_count=2 WHERE player_id='player'"
    )
    engine._conn.commit()

    loaded = engine.load("meta_check")
    assert loaded.ok is True
    stats_after = engine._row_dict("SELECT * FROM player_stats WHERE player_id='player'")
    assert int(stats_after["has_crossed_first_threshold"]) == 0
    assert int(stats_after["drift_count"]) == 1
    kw_after = json.loads(stats_after["recent_keywords"])
    assert ["veil"] in kw_after
    lines_after = json.loads(stats_after["last_npc_lines"])
    assert "mira" in lines_after
    assert "kaelen_lanternwright" not in lines_after

    # Legacy 0.0-1.0 save snapshot rescales smoothly to 0-1000 on load
    snap = json.loads(
        engine._row_dict("SELECT snapshot_json FROM save_slots WHERE slot_id='meta_check'")["snapshot_json"]
    )
    snap.pop("schema_version", None)
    snap["player_stats"]["resonance"] = 0.35
    snap["player_state"]["emotional_depth"] = 0.35
    engine._conn.execute(
        "INSERT OR REPLACE INTO save_slots (slot_id, label, snapshot_json) VALUES (?, ?, ?)",
        ("legacy_save", "Legacy 0.35", json.dumps(snap)),
    )
    engine._conn.commit()
    legacy_loaded = engine.load("legacy_save")
    assert legacy_loaded.scene["player"]["resonance"] == 350.0


def test_legacy_sqlite_migration_adds_resonance_columns_and_rescales_values(tmp_path: Path) -> None:
    db_file = tmp_path / "legacy_veil.sqlite"
    conn = sqlite3.connect(str(db_file))
    conn.executescript(
        """
        CREATE TABLE player_state (
            player_id TEXT PRIMARY KEY DEFAULT 'player',
            emotional_depth REAL DEFAULT 0.0,
            turns_taken INTEGER DEFAULT 0,
            unlocked_districts TEXT DEFAULT '["caetherra"]',
            dreams_seen INTEGER DEFAULT 0,
            veil_state TEXT DEFAULT 'calm',
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE player_stats (
            player_id TEXT PRIMARY KEY DEFAULT 'player',
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            resonance REAL DEFAULT 0.35,
            clarity INTEGER DEFAULT 10,
            empathy INTEGER DEFAULT 10,
            resolve INTEGER DEFAULT 10,
            perception INTEGER DEFAULT 10,
            veil_attunement INTEGER DEFAULT 10,
            emotional_tags TEXT DEFAULT '["warmth"]',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        INSERT INTO player_state (player_id, emotional_depth, turns_taken) VALUES ('player', 0.35, 1);
        INSERT INTO player_stats (player_id, resonance) VALUES ('player', 0.35);
        """
    )
    conn.commit()
    conn.close()

    engine = VeilGameEngine(repo_root=ROOT, db_path=db_file)
    try:
        scene = engine.scene()
        assert scene["player"]["resonance"] == 350.0
        ps = engine._row_dict("SELECT emotional_depth FROM player_state WHERE player_id='player'")
        assert float(ps["emotional_depth"]) == 350.0
        # Dialogue executes without OperationalError and advances migrated metadata
        reply = engine.play(Talk("mira", "Why do these warm lanterns flicker near the plaza?"))
        assert reply.ok is True
    finally:
        engine.close()


def test_schema_version_gates_legacy_migration_without_rescaling_low_v2_values(tmp_path: Path) -> None:
    db_file = tmp_path / "v2_veil.sqlite"
    engine = VeilGameEngine(repo_root=ROOT, db_path=db_file)
    try:
        assert int(engine._conn.execute("PRAGMA user_version").fetchone()[0]) == 2
        engine._conn.execute(
            "UPDATE player_stats SET resonance=0.5, has_crossed_first_threshold=1 WHERE player_id='player'"
        )
        engine._conn.execute("UPDATE player_state SET emotional_depth=0.5 WHERE player_id='player'")
        engine._conn.commit()
        assert engine.save("low_v2", "Low v2 0.5").ok is True
        snap = json.loads(
            engine._row_dict("SELECT snapshot_json FROM save_slots WHERE slot_id='low_v2'")["snapshot_json"]
        )
        assert snap["schema_version"] == 2
    finally:
        engine.close()

    reopened = VeilGameEngine(repo_root=ROOT, db_path=db_file)
    try:
        assert reopened.scene()["player"]["resonance"] == 0.5
        ps = reopened._row_dict("SELECT emotional_depth FROM player_state WHERE player_id='player'")
        assert float(ps["emotional_depth"]) == 0.5

        # Mutate away, then load v2 low-resonance save -> stays 0.5
        reopened.play(Use("echo_shard"))
        assert reopened.scene()["player"]["resonance"] == 6.5
        loaded_v2 = reopened.load("low_v2")
        assert loaded_v2.scene["player"]["resonance"] == 0.5

        # Legacy save without schema_version at 0.5 rescales once to 500.0
        legacy_snap = json.loads(
            reopened._row_dict("SELECT snapshot_json FROM save_slots WHERE slot_id='low_v2'")["snapshot_json"]
        )
        legacy_snap.pop("schema_version", None)
        reopened._conn.execute(
            "INSERT OR REPLACE INTO save_slots (slot_id, label, snapshot_json) VALUES (?, ?, ?)",
            ("legacy_05", "Legacy 0.5", json.dumps(legacy_snap)),
        )
        reopened._conn.commit()
        loaded_legacy = reopened.load("legacy_05")
        assert loaded_legacy.scene["player"]["resonance"] == 500.0
    finally:
        reopened.close()


def test_sealed_session_rejects_play_actions_until_reset() -> None:
    engine = _engine()
    engine._conn.execute("UPDATE player_stats SET resonance=0.0 WHERE player_id='player'")
    engine._conn.commit()

    shard_use = engine.play(Use("echo_shard"))
    assert shard_use.ok is False
    assert "sealed" in shard_use.message.lower()
    assert shard_use.scene["player"]["resonance"] == 0.0
    echo_item = next(item for item in shard_use.scene["inventory"] if item["id"] == "echo_shard")
    assert echo_item["quantity"] == 2

    blocked_talk = _talk(engine, text="I feel afraid — why is everything quiet?")
    assert blocked_talk.ok is False
    assert blocked_talk.scene["player"]["resonance"] == 0.0

    blocked_travel = engine.play(Travel("solstice_bazaar"))
    assert blocked_travel.ok is False
    assert blocked_travel.scene["world"]["current_location"]["id"] == "caetherra_plaza"

    reset = engine.reset_session()
    assert reset.ok is True
    assert reset.scene["player"]["resonance"] == 350.0
    assert _talk(engine, text="I wonder why the lanterns stay warm here?").ok is True
