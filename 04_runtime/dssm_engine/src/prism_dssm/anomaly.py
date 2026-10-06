"""DSSM anomaly detector — flag trials whose final stocks fall outside the per-cell distribution.

Stdlib-only. Reads JSONL events produced by `stress_test_runner.run_trial`
when `record_events=True` (same schema consumed by `analytics.summarize`).

Public API:
    detect_anomalies(events_path, *, z_threshold=2.0) -> list[dict]
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import analytics

_STOCKS = ("trust", "affection", "suspicion", "resistance")
_MIN_TRIALS = 3


def detect_anomalies(
    events_path: Path | str,
    *,
    z_threshold: float = 2.0,
) -> list[dict]:
    """For each (persona, ratio, seed) trial, compute z-scores of final stocks
    against its (persona, ratio) cell distribution; return list of anomalies.

    Cells with fewer than 3 trials are skipped silently.
    Stocks whose cell stdev is 0 are skipped (z-score undefined).
    """
    # Group events by trial; remember only the final post_l0_state per trial.
    by_trial: dict[tuple, list[dict]] = defaultdict(list)
    for ev in analytics.iter_events(Path(events_path)):
        key = (ev["persona"], ev["ratio"], ev["seed"])
        by_trial[key].append(ev)

    trial_finals: dict[tuple, dict[str, float]] = {}
    for key, evs in by_trial.items():
        evs.sort(key=lambda e: e["session"])
        trial_finals[key] = evs[-1]["post_l0_state"]

    # Group trial finals by (persona, ratio) cell.
    by_cell: dict[tuple, list[tuple]] = defaultdict(list)
    for (persona, ratio, seed), final in trial_finals.items():
        by_cell[(persona, ratio)].append((seed, final))

    anomalies: list[dict] = []
    for (persona, ratio), trials in by_cell.items():
        if len(trials) < _MIN_TRIALS:
            continue

        # Compute per-stock cell mean and sample stdev.
        cell_stats: dict[str, tuple[float, float]] = {}
        for stock in _STOCKS:
            values = [final[stock] for _seed, final in trials]
            mean = statistics.mean(values)
            sd = statistics.stdev(values)
            cell_stats[stock] = (mean, sd)

        for seed, final in trials:
            offending: list[dict[str, Any]] = []
            for stock in _STOCKS:
                mean, sd = cell_stats[stock]
                if sd == 0:
                    continue
                value = final[stock]
                z = (value - mean) / sd
                if abs(z) >= z_threshold:
                    offending.append(
                        {
                            "stock": stock,
                            "value": value,
                            "cell_mean": mean,
                            "cell_stdev": sd,
                            "z_score": z,
                        },
                    )
            if offending:
                anomalies.append(
                    {
                        "persona": persona,
                        "ratio": ratio,
                        "seed": seed,
                        "anomalous_stocks": offending,
                    },
                )

    return anomalies
