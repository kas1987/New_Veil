"""Tests for prism_dssm.calibrator grid-search."""

from __future__ import annotations

from pathlib import Path

import pytest
from prism_dssm import calibrator

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


def test_calibrate_smoke():
    out = calibrator.calibrate(
        CONFIG_DIR,
        grid={
            "trust_decay": [0.008, 0.012],
            "trust_baseline": [25.0, 30.0],
        },
        target_persona="Mira",
        target_metric="win_rate",
        target_value=1.0,
        sessions=5,
        ratios=(5.0,),
        seeds=(11, 13),
    )
    assert "best" in out
    assert "all_results" in out
    assert len(out["all_results"]) == 4  # 2 x 2 grid
    # Sorted ascending by score.
    scores = [r["score"] for r in out["all_results"]]
    assert scores == sorted(scores)
    # Best should have score <= at least one other entry.
    assert out["best"]["score"] <= out["all_results"][-1]["score"]
    # Each result has params dict matching the grid keys.
    for r in out["all_results"]:
        assert set(r["params"].keys()) == {"trust_decay", "trust_baseline"}


def test_calibrate_invalid_field_raises():
    with pytest.raises(ValueError, match="not on CoreParams"):
        calibrator.calibrate(
            CONFIG_DIR,
            grid={"nonexistent_field": [0.1]},
            target_persona="Mira",
            target_metric="win_rate",
            target_value=1.0,
            sessions=5,
            ratios=(5.0,),
            seeds=(11,),
        )
