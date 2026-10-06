"""Parameter-sensitivity report for CoreParams.

For each float-typed CoreParams field, perturbs the value by +/- delta_pct,
re-runs a small persona x ratio x seed grid via run_trial, and reports the
signed sensitivity = (plus_win_rate - minus_win_rate) / (2 * delta_pct).

Stdlib only. Re-uses the layered pipeline through stress_test_runner.run_trial.
"""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Any

from .config_loader import load_config_dir
from .models import CoreParams
from .stress_test_runner import ScenarioConfig, run_trial
from .veil_effects import VeilStateMachine


def _float_fields() -> list[str]:
    """Return names of CoreParams fields whose declared type is float."""
    out: list[str] = []
    for f in fields(CoreParams):
        # Type may arrive as the class `float` or the string "float" depending on
        # how `from __future__ import annotations` resolved.
        t = f.type
        if t is float or t == "float":
            out.append(f.name)
    return out


def _win_rate(
    cfg: Any,
    params: CoreParams,
    *,
    sessions: int,
    ratios: tuple[float, ...],
    seeds: tuple[int, ...],
    target_persona: str | None,
) -> float:
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    if target_persona is not None:
        persona_items = [(target_persona, cfg.personas[target_persona])]
    else:
        persona_items = list(cfg.personas.items())

    wins = 0
    total = 0
    for _name, persona in persona_items:
        for ratio in ratios:
            for seed in seeds:
                machine.tick = 0
                trial = run_trial(
                    persona,
                    ScenarioConfig(
                        sessions=sessions,
                        pos_to_neg_ratio=ratio,
                        seed=seed,
                    ),
                    params=params,
                    veil_machine=machine,
                )
                wins += int(trial.win)
                total += 1
    return wins / total if total else 0.0


def sensitivity_report(
    config_dir: Path,
    *,
    fields: list[str] | None = None,
    delta_pct: float = 0.10,
    sessions: int = 20,
    ratios: tuple[float, ...] = (5.0,),
    seeds: tuple[int, ...] = (11, 13, 17),
    target_persona: str | None = None,
) -> dict:
    """Per-field +/- delta_pct perturbation report.

    For each float field on CoreParams, runs the small grid with the field set
    to baseline*(1+delta_pct) and baseline*(1-delta_pct), reports the resulting
    win rates, and a signed sensitivity score.
    """
    cfg = load_config_dir(config_dir)
    target_fields = fields if fields is not None else _float_fields()

    baseline_params = CoreParams()
    baseline_win_rate = _win_rate(
        cfg,
        baseline_params,
        sessions=sessions,
        ratios=ratios,
        seeds=seeds,
        target_persona=target_persona,
    )

    field_reports: list[dict] = []
    for name in target_fields:
        baseline_value = float(getattr(baseline_params, name))
        plus_value = baseline_value * (1.0 + delta_pct)
        minus_value = baseline_value * (1.0 - delta_pct)

        plus_params = CoreParams(**{name: plus_value})
        minus_params = CoreParams(**{name: minus_value})

        plus_rate = _win_rate(
            cfg,
            plus_params,
            sessions=sessions,
            ratios=ratios,
            seeds=seeds,
            target_persona=target_persona,
        )
        minus_rate = _win_rate(
            cfg,
            minus_params,
            sessions=sessions,
            ratios=ratios,
            seeds=seeds,
            target_persona=target_persona,
        )

        denom = 2.0 * delta_pct if delta_pct else 1.0
        sensitivity = (plus_rate - minus_rate) / denom

        field_reports.append(
            {
                "field": name,
                "baseline_value": baseline_value,
                "plus_value": plus_value,
                "plus_win_rate": plus_rate,
                "minus_value": minus_value,
                "minus_win_rate": minus_rate,
                "sensitivity": sensitivity,
            },
        )

    field_reports.sort(key=lambda r: abs(r["sensitivity"]), reverse=True)

    return {
        "baseline_win_rate": baseline_win_rate,
        "delta_pct": delta_pct,
        "fields": field_reports,
    }
