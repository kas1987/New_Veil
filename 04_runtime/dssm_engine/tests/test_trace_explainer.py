"""Tests for trace_explainer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from prism_dssm.trace_explainer import explain_trial, format_narrative


def _write_synthetic(
    path: Path, persona: str, seed: int, ratio: float, trusts: list[float],
) -> None:
    """Write a synthetic JSONL of events with the given trust trajectory."""
    with path.open("w", encoding="utf-8") as f:
        for i, t in enumerate(trusts):
            row = {
                "run_id": "synthetic",
                "persona": persona,
                "seed": seed,
                "ratio": ratio,
                "session": i,
                "signal": "compliment",
                "l1_deltas": {},
                "post_l5pre_deltas": {},
                "post_l0_state": {
                    "trust": t,
                    "affection": 25.0,
                    "suspicion": 30.0,
                    "resistance": 30.0,
                },
                "veil_state": "Calm",
                "override_fired": False,
                "network_neighbors_after": None,
            }
            f.write(json.dumps(row) + "\n")


def test_explain_trial_synthetic(tmp_path):
    events = tmp_path / "events.jsonl"
    _write_synthetic(events, "Mira", 11, 5.0, [30.0, 40.0, 65.0, 50.0, 70.0])

    result = explain_trial(events, persona="Mira", seed=11, ratio=5.0)

    assert result["verdict"] == "won"
    breakthroughs = [
        tp for tp in result["turning_points"] if tp["type"] == "trust_breakthrough"
    ]
    assert len(breakthroughs) == 1
    assert breakthroughs[0]["session"] == 2
    assert len(result["lines"]) == 5


def test_explain_trial_filter_no_match_raises(tmp_path):
    events = tmp_path / "events.jsonl"
    _write_synthetic(events, "Mira", 11, 5.0, [30.0, 40.0, 50.0])

    with pytest.raises(ValueError):
        explain_trial(events, persona="Mira", seed=999, ratio=5.0)


def test_format_narrative_includes_verdict(tmp_path):
    events = tmp_path / "events.jsonl"
    _write_synthetic(events, "Mira", 11, 5.0, [30.0, 40.0, 65.0, 50.0, 70.0])

    result = explain_trial(events, persona="Mira", seed=11, ratio=5.0)
    text = format_narrative(result)

    assert "Verdict:" in text
    assert "Mira" in text
