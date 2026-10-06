"""End-to-end stress test runner — full layered pipeline.

Pipeline per turn (one persona, one signal):
    raw signal name
      → L1 persona_filters.filter_signal           ({stock: delta} dict)
      → L2 persona_filters.apply_attachment        (anxious/avoidant/secure)
      → L3a veil_effects.corrupt_deltas            (signal noise)
      → L5 narrative_overrides.pre_apply           (override rules pre)
      → L0 dssm_core.apply_deltas                  (resistance-gated update)
      → L3b dssm_core.decay_step(decay_multiplier) (entropy decay)
      → L3c veil_effects.DarkQuasar.apply_gravity  (emotional gravity drag)
      → L4 network.propagate                       (leak focal delta to neighbors)
      → L5 narrative_overrides.post_apply          (history)
      → L5 narrative_overrides.tick_pending        (delayed effects fire)

Win condition (per persona, per scenario):
    Trust > 60 ∧ Suspicion < 40 ∧ Resistance < 35 after N sessions.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

VAR_WINDOW = 10
_VAR_STOCKS = ("trust", "affection", "suspicion", "resistance")

from . import analytics
from .config_loader import load_config_dir
from .dssm_core import apply_deltas, decay_step
from .models import CoreParams, CoreState
from .narrative_overrides import (
    make_context,
    post_apply,
    pre_apply,
    tick_pending,
)
from .network import Network, propagate
from .persona_filters import (
    PersonaConfig,
    apply_attachment,
    filter_signal,
)
from .veil_effects import (
    DarkQuasar,
    EntropyConfig,
    EntropyEngine,
    QuasarConfig,
    VeilStateMachine,
    corrupt_deltas,
)

SIGNAL_POOL_POS = ["compliment", "support", "honesty", "vulnerability"]
SIGNAL_POOL_NEG = ["silence", "criticism", "deception"]


@dataclass
class ScenarioConfig:
    sessions: int = 50
    pos_to_neg_ratio: float = 5.0
    seed: int = 42
    initial_state: dict[str, float] | None = None


@dataclass
class TrialResult:
    persona: str
    final_state: dict[str, float]
    win: bool
    sessions: int
    trajectory: list[dict[str, float]] = field(default_factory=list)


def _draw_signal(rng: random.Random, ratio: float) -> str:
    p_positive = ratio / (ratio + 1.0)
    pool = SIGNAL_POOL_POS if rng.random() < p_positive else SIGNAL_POOL_NEG
    return rng.choice(pool)


def run_trial(
    persona: PersonaConfig,
    scenario: ScenarioConfig,
    *,
    params: CoreParams | None = None,
    veil_machine: VeilStateMachine | None = None,
    entropy: EntropyEngine | None = None,
    quasar: DarkQuasar | None = None,
    record_trajectory: bool = False,
    network: Network | None = None,
    focal: str = "Player",
    record_events: bool = False,
    events_path: Path | None = None,
    run_id: str | None = None,
) -> TrialResult:
    """Run one persona through one scenario through the full layer stack."""
    rng = random.Random(scenario.seed)
    params = params or CoreParams()
    entropy = entropy or EntropyEngine(
        EntropyConfig(),
        random.Random(scenario.seed + 1),
    )
    quasar = quasar or DarkQuasar(QuasarConfig(), random.Random(scenario.seed + 2))

    init = scenario.initial_state or persona.initial_state or {}
    state = CoreState(
        trust=float(init.get("trust", 30.0)),
        affection=float(init.get("affection", 25.0)),
        suspicion=float(init.get("suspicion", 50.0)),
        resistance=float(init.get("resistance", 70.0)),
    )

    ctx = make_context(persona.persona, persona.override_rules)
    traj: list[dict[str, float]] = []

    trait_prior = persona.trait_prior or None
    delta_history: dict[str, list[float]] = {k: [] for k in _VAR_STOCKS}

    events_fh = None
    if record_events and events_path is not None:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_fh = events_path.open("a", encoding="utf-8")

    try:
        for session in range(scenario.sessions):
            # pre captures session start; propagate() leaks the full-session delta to neighbors.
            pre_snapshot = CoreState(**state.as_dict()) if network is not None else None
            pre_state_for_var = state.as_dict()

            signal = _draw_signal(rng, scenario.pos_to_neg_ratio)

            # L1
            deltas = filter_signal(persona, signal)
            l1_snap = dict(deltas) if record_events else None
            # L2
            deltas = apply_attachment(
                deltas,
                persona.attachment_state,
                persona.attachment_modifiers,
            )
            # L3a
            veil = veil_machine.current() if veil_machine else None
            if veil is not None:
                deltas = corrupt_deltas(deltas, veil, rng)
            # L5 pre
            pre_l5_in = dict(deltas) if record_events else None
            deltas = pre_apply(ctx, signal, deltas)
            l5pre_snap = dict(deltas) if record_events else None
            override_fired = (pre_l5_in != l5pre_snap) if record_events else False
            # L0 apply
            apply_deltas(state, deltas, params)
            # L3b decay (toward trait_prior when present)
            decay_step(
                state,
                params,
                decay_multiplier=entropy.decay_multiplier(),
                trait_prior=trait_prior,
            )
            # L3c quasar gravity
            excess = quasar.assess(state)
            quasar.apply_gravity(state, excess)
            # L5 post + delayed
            post_apply(ctx, signal)
            due = tick_pending(ctx)
            if due:
                apply_deltas(state, due, params)

            if veil_machine is not None:
                veil_machine.advance()

            # Update per-stock running variance over recent session deltas.
            post_state = state.as_dict()
            for k in _VAR_STOCKS:
                d = post_state[k] - pre_state_for_var[k]
                hist = delta_history[k]
                hist.append(d)
                if len(hist) > VAR_WINDOW:
                    del hist[0]
                if len(hist) >= 2:
                    mean = sum(hist) / len(hist)
                    var = sum((x - mean) ** 2 for x in hist) / (len(hist) - 1)
                else:
                    var = 0.0
                setattr(state, f"{k}_var", var)

            # L4 network propagation — leak focal delta to neighbors.
            neighbors_after: dict[str, dict[str, float]] | None = None
            if network is not None and pre_snapshot is not None:
                propagate(network, focal, pre_snapshot, state)
                if record_events:
                    neighbors_after = {
                        n: network.agents[n].as_dict()
                        for n in network.agents
                        if n != focal
                    }

            if record_trajectory:
                traj.append({"session": session, **state.as_dict()})

            if events_fh is not None:
                row = {
                    "run_id": run_id,
                    "persona": persona.persona,
                    "seed": scenario.seed,
                    "ratio": scenario.pos_to_neg_ratio,
                    "session": session,
                    "signal": signal,
                    "l1_deltas": l1_snap,
                    "post_l5pre_deltas": l5pre_snap,
                    "post_l0_state": state.as_dict(),
                    "veil_state": veil.name if veil is not None else None,
                    "override_fired": override_fired,
                    "network_neighbors_after": neighbors_after,
                }
                events_fh.write(json.dumps(row, separators=(",", ":")) + "\n")
    finally:
        if events_fh is not None:
            events_fh.close()

    return TrialResult(
        persona=persona.persona,
        final_state=state.as_dict(),
        win=state.win_condition(),
        sessions=scenario.sessions,
        trajectory=traj,
    )


def sweep(
    config_dir: str | Path,
    *,
    sessions: int | None = None,
    ratios: tuple[float, ...] | None = None,
    seeds: tuple[int, ...] | None = None,
    record_events: bool = False,
    run_id: str | None = None,
    events_dir: Path | None = None,
) -> dict[str, Any]:
    """Sweep every persona × ratio × seed; report win rate per cell.

    Defaults are sourced from configs/stress_test_default.json when present;
    explicit kwargs override.
    """
    cfg = load_config_dir(config_dir)
    veil_machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)

    st = cfg.stress_test or {}
    if sessions is None:
        sessions = int(st.get("sessions", 50))
    if ratios is None:
        ratios = tuple(
            float(r) for r in st.get("ratios", (2.0, 3.0, 4.0, 5.0, 6.0, 7.0))
        )
    if seeds is None:
        seeds = tuple(int(s) for s in st.get("seeds", (11, 13, 17, 19, 23)))

    events_path: Path | None = None
    if record_events:
        run_id = run_id or f"sweep-{int(time.time() * 1000)}"
        if events_dir is None:
            events_dir = Path(config_dir).resolve().parent / "results" / "events"
        events_path = events_dir / f"{run_id}.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        # Truncate any prior file for this run_id so writes are append-only-fresh.
        if events_path.exists():
            events_path.unlink()

    out: dict[str, Any] = {"sessions": sessions, "cells": []}
    for name, persona in cfg.personas.items():
        for ratio in ratios:
            wins = 0
            for seed in seeds:
                veil_machine.tick = 0
                trial = run_trial(
                    persona,
                    ScenarioConfig(
                        sessions=sessions,
                        pos_to_neg_ratio=ratio,
                        seed=seed,
                    ),
                    veil_machine=veil_machine,
                    network=cfg.network,
                    record_events=record_events,
                    events_path=events_path,
                    run_id=run_id,
                )
                wins += int(trial.win)
            out["cells"].append(
                {
                    "persona": name,
                    "ratio": ratio,
                    "seeds": len(seeds),
                    "wins": wins,
                    "win_rate": wins / len(seeds),
                },
            )

    if record_events and events_path is not None:
        out["run_id"] = run_id
        out["events_path"] = str(events_path)
        out["analytics"] = analytics.summarize(events_path)

    return out


if __name__ == "__main__":
    base = Path(__file__).resolve().parents[2]
    cfg_dir = base / "configs"
    result = sweep(cfg_dir)
    out_path = base / "results"
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "sweep_summary.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )
    for cell in result["cells"]:
        print(
            f"{cell['persona']:>8} ratio={cell['ratio']:>3.1f}  "
            f"wins={cell['wins']}/{cell['seeds']}  rate={cell['win_rate']:.2f}",
        )
