"""Psychometric calibration evals and observatory data-layer regression tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
EVAL_MOD = load_module("veil_eval_runner", ROOT / "14_psychometrics" / "eval_runner.py")
OBS_DATA = load_module("veil_observatory_data", ROOT / "07_ui" / "observatory" / "data.py")


def test_psychometric_calibration_archetypes_pass() -> None:
    corpus_path = ROOT / EVAL_MOD.CORPUS_REL
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    scripts = corpus["archetype_scripts"]
    assert scripts

    for script in scripts:
        result = EVAL_MOD.run_archetype(script)
        assert result["passed"] is True, (
            f"Archetype {script['id']} failed: {result['failures']}"
        )
        assert result["exploit_flags"] == [], (
            f"Archetype {script['id']} triggered exploit flags: {result['exploit_flags']}"
        )


def test_observatory_data_helpers_isolated(tmp_path: Path, monkeypatch) -> None:
    log_path = tmp_path / "replay.jsonl"
    log_path.write_text(
        "\n".join(
            [
                json.dumps({"timestamp": "2026-11-23T12:00:00Z", "type": "symbolic_event", "agent": "mira"}),
                "{bad json line",
                json.dumps({"timestamp": "2026-11-23T12:01:00Z", "type": "dream_generated", "agent_id": "lyra"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    items = OBS_DATA._iter_replay(log_path)
    assert len(items) == 2

    monkeypatch.setattr(OBS_DATA, "_LOG_PATH", tmp_path / "missing.jsonl")
    assert OBS_DATA.read_replay() == "No replay logs yet."
    assert OBS_DATA.read_events() == [["(no replay log)", "", "", ""]]

    monkeypatch.setattr(OBS_DATA, "_LOG_PATH", log_path)
    assert "symbolic_event" in OBS_DATA.read_replay(limit=5)
    events = OBS_DATA.read_events(limit=10)
    assert len(events) == 2
    assert events[0][1] == "dream_generated"

    db_path = tmp_path / "obs_test.sqlite"
    monkeypatch.setattr(OBS_DATA._memory_router, "DB_PATH", db_path)
    assert OBS_DATA.read_relationships_chart_data() == []
    assert OBS_DATA.read_agent_player_relationship("mira") == {}
    assert "no database" in OBS_DATA.read_relationships()[0][0]

    schema_sql = (ROOT / "03_memory" / "schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.execute(
            """
            INSERT INTO relationships (agent_a, agent_b, trust, affection, suspicion, resistance, interactions)
            VALUES ('mira', 'player', 64.5, 55.0, 8.0, 42.0, 3)
            """
        )
        conn.commit()

    rows = OBS_DATA.read_relationships()
    assert len(rows) == 1
    assert rows[0][:2] == ["mira", "player"]

    chart_rows = OBS_DATA.read_relationships_chart_data()
    assert len(chart_rows) == 1
    assert chart_rows[0]["resistance"] == 42.0

    dyad = OBS_DATA.read_agent_player_relationship("mira")
    assert dyad["trust"] == 64.5
    assert dyad["interactions"] == 3
