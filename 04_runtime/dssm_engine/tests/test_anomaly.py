"""Tests for prism_dssm.anomaly.detect_anomalies."""

from __future__ import annotations

import json
from pathlib import Path

from prism_dssm.anomaly import detect_anomalies


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def _make_trial_rows(
    persona: str,
    ratio: float,
    seed: int,
    final_state: dict[str, float],
    sessions: int = 3,
) -> list[dict]:
    """Build a list of synthetic event rows; only the last session's state matters."""
    rows = []
    for s in range(sessions):
        # Earlier sessions can use a placeholder state; only the final one is read.
        state = (
            final_state
            if s == sessions - 1
            else {"trust": 0.0, "affection": 0.0, "suspicion": 0.0, "resistance": 0.0}
        )
        rows.append(
            {
                "persona": persona,
                "ratio": ratio,
                "seed": seed,
                "session": s,
                "post_l0_state": state,
            },
        )
    return rows


def test_detect_anomalies_synthetic(tmp_path):
    path = tmp_path / "events.jsonl"
    rows: list[dict] = []
    # Four tightly-clustered trials around trust=30, plus one outlier at trust=90.
    cluster = [
        (1, 29.0),
        (2, 30.0),
        (3, 31.0),
        (4, 30.5),
        (5, 29.5),
        (6, 30.2),
        (7, 30.8),
        (8, 29.8),
    ]
    for seed, trust in cluster:
        rows.extend(
            _make_trial_rows(
                "Mira",
                5.0,
                seed,
                {
                    "trust": trust,
                    "affection": 25.0,
                    "suspicion": 50.0,
                    "resistance": 40.0,
                },
            ),
        )
    # The outlier
    rows.extend(
        _make_trial_rows(
            "Mira",
            5.0,
            99,
            {"trust": 90.0, "affection": 25.0, "suspicion": 50.0, "resistance": 40.0},
        ),
    )
    _write_jsonl(path, rows)

    anomalies = detect_anomalies(path, z_threshold=2.0)
    assert len(anomalies) == 1
    a = anomalies[0]
    assert a["persona"] == "Mira"
    assert a["ratio"] == 5.0
    assert a["seed"] == 99
    trust_entries = [s for s in a["anomalous_stocks"] if s["stock"] == "trust"]
    assert len(trust_entries) == 1
    assert abs(trust_entries[0]["z_score"]) >= 2.0
    assert trust_entries[0]["value"] == 90.0


def test_no_anomalies_when_uniform(tmp_path):
    path = tmp_path / "events.jsonl"
    rows: list[dict] = []
    final = {"trust": 50.0, "affection": 25.0, "suspicion": 30.0, "resistance": 40.0}
    for seed in (1, 2, 3, 4, 5):
        rows.extend(_make_trial_rows("Shadow", 4.0, seed, final))
    _write_jsonl(path, rows)

    anomalies = detect_anomalies(path, z_threshold=2.0)
    assert anomalies == []
