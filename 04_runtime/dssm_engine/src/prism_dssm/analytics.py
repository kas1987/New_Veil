"""DSSM analytics — per-cell metrics from JSONL event logs.

Stdlib-only. Reads `results/events/<run_id>.jsonl` produced by
`stress_test_runner.run_trial` when `record_events=True`.

Public API:
    iter_events(path)              — stream JSONL rows
    metrics_for_trajectory(events) — single-trial metrics
    aggregate_cell(trajectories)   — per-(persona,ratio) summary with 95% CIs
    summarize(path)                — top-level entrypoint
    t_critical(df, alpha=0.05)     — Student's t critical value
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

# Two-sided 95% (alpha=0.05) Student's t critical values.
_T_TABLE_95: dict[int, float] = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    11: 2.201,
    12: 2.179,
    13: 2.160,
    14: 2.145,
    15: 2.131,
    16: 2.120,
    17: 2.110,
    18: 2.101,
    19: 2.093,
    20: 2.086,
    25: 2.060,
    30: 2.042,
}
_Z_95 = 1.96


def t_critical(df: int, alpha: float = 0.05) -> float:
    """Two-sided critical value. Only alpha=0.05 supported; df>30 → z."""
    if alpha != 0.05:
        raise ValueError("only alpha=0.05 supported")
    if df <= 0:
        raise ValueError("df must be positive")
    if df in _T_TABLE_95:
        return _T_TABLE_95[df]
    if df > 30:
        return _Z_95
    # Interpolate between nearest tabled values.
    keys = sorted(_T_TABLE_95)
    lo = max(k for k in keys if k <= df)
    hi = min(k for k in keys if k >= df)
    if lo == hi:
        return _T_TABLE_95[lo]
    frac = (df - lo) / (hi - lo)
    return _T_TABLE_95[lo] + frac * (_T_TABLE_95[hi] - _T_TABLE_95[lo])


def iter_events(path: Path) -> Iterator[dict]:
    with Path(path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


_STOCKS = ("trust", "affection", "suspicion", "resistance")


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = min(len(xs), len(ys))
    if n < 2:
        return None
    mx = sum(xs[:n]) / n
    my = sum(ys[:n]) / n
    num = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    dx2 = sum((xs[i] - mx) ** 2 for i in range(n))
    dy2 = sum((ys[i] - my) ** 2 for i in range(n))
    denom = math.sqrt(dx2 * dy2)
    if denom == 0.0:
        return None
    return num / denom


def metrics_for_trajectory(events: list[dict]) -> dict[str, Any]:
    """Compute single-trial metrics. Events should be sorted by session."""
    states = [e["post_l0_state"] for e in events]
    if not states:
        return {
            "time_to_trust_60": None,
            "peak_suspicion": 0.0,
            "mean_resistance": 0.0,
            "oscillation": 0,
            "reliability_split_half": None,
            "final": None,
        }
    trusts = [s["trust"] for s in states]
    sus = [s["suspicion"] for s in states]
    res = [s["resistance"] for s in states]
    ttt = next((i for i, t in enumerate(trusts) if t > 60.0), None)
    deltas = [trusts[i + 1] - trusts[i] for i in range(len(trusts) - 1)]
    osc = 0
    for i in range(len(deltas) - 1):
        a, b = deltas[i], deltas[i + 1]
        if a == 0 or b == 0:
            continue
        if (a > 0) != (b > 0):
            osc += 1

    # Split-half (odd vs even sessions) Pearson correlation per stock.
    if len(states) >= 4:
        reliability: dict[str, float | None] | None = {}
        for k in _STOCKS:
            vals = [s.get(k, 0.0) for s in states]
            evens = vals[0::2]
            odds = vals[1::2]
            reliability[k] = _pearson(evens, odds)
    else:
        reliability = None

    return {
        "time_to_trust_60": ttt,
        "peak_suspicion": max(sus),
        "mean_resistance": statistics.mean(res),
        "oscillation": osc,
        "reliability_split_half": reliability,
        "final": states[-1],
    }


def _ci95(values: list[float]) -> dict[str, Any]:
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "ci95": [0.0, 0.0], "stdev": 0.0, "n": 0}
    m = statistics.mean(values)
    if n == 1:
        return {"mean": m, "ci95": [m, m], "stdev": 0.0, "n": 1}
    sd = statistics.stdev(values)
    half = t_critical(n - 1) * sd / math.sqrt(n)
    return {"mean": m, "ci95": [m - half, m + half], "stdev": sd, "n": n}


def aggregate_cell(trajectories: list[list[dict]]) -> dict[str, Any]:
    per = [metrics_for_trajectory(t) for t in trajectories]
    finals = [p["final"] for p in per if p["final"] is not None]

    def _won(f: dict) -> bool:
        return f["trust"] > 60.0 and f["suspicion"] < 40.0 and f["resistance"] < 35.0

    out: dict[str, Any] = {
        "n": len(per),
        "win_rate": (sum(1 for f in finals if _won(f)) / len(per)) if per else 0.0,
    }
    for stock in _STOCKS:
        out[stock] = _ci95([f[stock] for f in finals])
        var_key = f"{stock}_var"
        var_vals = [f[var_key] for f in finals if var_key in f]
        out[var_key + "_mean"] = statistics.mean(var_vals) if var_vals else 0.0

    rel_means: dict[str, float | None] = {}
    for stock in _STOCKS:
        vals = [
            p["reliability_split_half"][stock]
            for p in per
            if p["reliability_split_half"] is not None
            and p["reliability_split_half"].get(stock) is not None
        ]
        rel_means[stock] = statistics.mean(vals) if vals else None
    out["reliability_split_half_mean"] = rel_means

    ttt_vals = [p["time_to_trust_60"] for p in per if p["time_to_trust_60"] is not None]
    out["time_to_trust_60_mean"] = statistics.mean(ttt_vals) if ttt_vals else None
    out["time_to_trust_60_n_reached"] = len(ttt_vals)
    out["peak_suspicion_mean"] = (
        statistics.mean([p["peak_suspicion"] for p in per]) if per else 0.0
    )
    out["oscillation_mean"] = (
        statistics.mean([p["oscillation"] for p in per]) if per else 0.0
    )
    return out


def summarize(path: str | Path) -> dict[str, Any]:
    """Read JSONL, group by (persona, ratio, seed)→trajectory, then aggregate by cell."""
    by_trial: dict[tuple, list[dict]] = defaultdict(list)
    for ev in iter_events(Path(path)):
        key = (ev["persona"], ev["ratio"], ev["seed"])
        by_trial[key].append(ev)

    by_cell: dict[tuple, list[list[dict]]] = defaultdict(list)
    for (persona, ratio, _seed), evs in by_trial.items():
        evs.sort(key=lambda e: e["session"])
        by_cell[(persona, ratio)].append(evs)

    cells = []
    for (persona, ratio), trajs in sorted(by_cell.items()):
        cells.append({"persona": persona, "ratio": ratio, **aggregate_cell(trajs)})
    return {"cells": cells}
