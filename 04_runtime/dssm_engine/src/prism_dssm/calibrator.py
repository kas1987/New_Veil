"""Parameter calibrator — grid-search small CoreParams overrides against a target metric.

Stdlib only. Iterates the cartesian product of `grid`, runs `run_trial` for each
(ratio, seed) on the target persona, aggregates trajectories with `analytics.aggregate_cell`,
and ranks combos by absolute distance from `target_value`.

Public API:
    calibrate(config_dir, *, grid, target_persona, target_metric, target_value,
              sessions=30, ratios=(5.0,), seeds=(11, 13, 17)) -> dict
"""

from __future__ import annotations

import dataclasses
import itertools
from pathlib import Path
from typing import Any

from . import analytics
from .config_loader import load_config_dir
from .models import CoreParams
from .stress_test_runner import ScenarioConfig, run_trial
from .veil_effects import VeilStateMachine

_VALID_METRICS = {"win_rate", "time_to_trust_60_mean"}


def _coreparams_fields() -> set[str]:
    return {f.name for f in dataclasses.fields(CoreParams)}


def _trajectory_from_trial(trial_traj: list[dict]) -> list[dict]:
    """Convert a recorded `run_trial(record_trajectory=True)` traj into the
    event-shaped list `analytics.metrics_for_trajectory` expects."""
    out = []
    for row in trial_traj:
        out.append(
            {
                "session": row["session"],
                "post_l0_state": {
                    "trust": row["trust"],
                    "affection": row["affection"],
                    "suspicion": row["suspicion"],
                    "resistance": row["resistance"],
                },
            },
        )
    return out


def calibrate(
    config_dir: Path,
    *,
    grid: dict[str, list[float]],
    target_persona: str,
    target_metric: str,
    target_value: float,
    sessions: int = 30,
    ratios: tuple[float, ...] = (5.0,),
    seeds: tuple[int, ...] = (11, 13, 17),
) -> dict:
    """Grid search over CoreParams overrides; return best combo + ranked results."""
    if target_metric not in _VALID_METRICS:
        raise ValueError(
            f"target_metric must be one of {_VALID_METRICS}, got {target_metric!r}",
        )

    valid_fields = _coreparams_fields()
    bad = [k for k in grid if k not in valid_fields]
    if bad:
        raise ValueError(
            f"grid contains keys not on CoreParams: {bad}. "
            f"Valid fields: {sorted(valid_fields)}",
        )

    if not grid:
        raise ValueError("grid must be non-empty")

    cfg = load_config_dir(config_dir)
    if target_persona not in cfg.personas:
        raise ValueError(
            f"target_persona {target_persona!r} not found in configs; "
            f"available: {sorted(cfg.personas)}",
        )
    persona = cfg.personas[target_persona]

    keys = list(grid.keys())
    value_lists = [grid[k] for k in keys]

    veil_machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)

    results: list[dict] = []
    for combo_vals in itertools.product(*value_lists):
        combo = dict(zip(keys, combo_vals, strict=False))
        params = CoreParams(**combo)

        trajectories: list[list[dict]] = []
        for ratio in ratios:
            for seed in seeds:
                veil_machine.tick = 0
                trial = run_trial(
                    persona,
                    ScenarioConfig(
                        sessions=sessions,
                        pos_to_neg_ratio=ratio,
                        seed=seed,
                    ),
                    params=params,
                    veil_machine=veil_machine,
                    record_trajectory=True,
                )
                trajectories.append(_trajectory_from_trial(trial.trajectory))

        cell = analytics.aggregate_cell(trajectories)
        metric_value = cell.get(target_metric)
        # Guard for None (e.g. time_to_trust_60_mean when no trial reached 60).
        if metric_value is None:
            score = float("inf")
            metric_for_record: Any = None
        else:
            score = abs(float(metric_value) - float(target_value))
            metric_for_record = float(metric_value)

        results.append(
            {
                "params": combo,
                "score": score,
                "metric_value": metric_for_record,
            },
        )

    results.sort(key=lambda r: r["score"])
    best = results[0] if results else None
    return {"best": best, "all_results": results}
