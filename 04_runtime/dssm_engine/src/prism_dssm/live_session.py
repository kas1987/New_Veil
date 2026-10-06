"""Single-step DSSM session runner — drives the full L1→L5 pipeline one signal at a time.

Companion to stress_test_runner.run_trial: same layer order, same math, but
exposed as a stateful object so an interactive frontend can step a session
manually instead of running an N-session sweep.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

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
from .stress_test_runner import _VAR_STOCKS, VAR_WINDOW
from .veil_effects import (
    DarkQuasar,
    EntropyConfig,
    EntropyEngine,
    QuasarConfig,
    VeilStateMachine,
    corrupt_deltas,
)


@dataclass
class StepResult:
    session: int
    signal: str
    l1_deltas: dict[str, float]
    post_l5pre_deltas: dict[str, float]
    post_l0_state: dict[str, float]
    veil_state: str | None
    override_fired: bool
    neighbors: dict[str, dict[str, float]] | None


@dataclass
class SessionRunner:
    persona: PersonaConfig
    params: CoreParams = field(default_factory=CoreParams)
    network: Network | None = None
    focal: str = "Player"
    seed: int = 42
    veil_machine: VeilStateMachine | None = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self._entropy = EntropyEngine(EntropyConfig(), random.Random(self.seed + 1))
        self._quasar = DarkQuasar(QuasarConfig(), random.Random(self.seed + 2))

        init = self.persona.initial_state or {}
        self.state = CoreState(
            trust=float(init.get("trust", 30.0)),
            affection=float(init.get("affection", 25.0)),
            suspicion=float(init.get("suspicion", 50.0)),
            resistance=float(init.get("resistance", 70.0)),
        )
        self._ctx = make_context(self.persona.persona, self.persona.override_rules)
        self._trait_prior = self.persona.trait_prior or None
        self._delta_history: dict[str, list[float]] = {k: [] for k in _VAR_STOCKS}
        self._session = 0
        self._history: list[StepResult] = []
        self._history_max = 50
        if self.veil_machine is not None:
            self.veil_machine.tick = 0

    def step(self, signal: str) -> StepResult:
        pre_snapshot = (
            CoreState(**self.state.as_dict()) if self.network is not None else None
        )
        pre_state_for_var = self.state.as_dict()

        deltas = filter_signal(self.persona, signal)
        l1_snap = dict(deltas)
        deltas = apply_attachment(
            deltas,
            self.persona.attachment_state,
            self.persona.attachment_modifiers,
        )

        veil = self.veil_machine.current() if self.veil_machine else None
        if veil is not None:
            deltas = corrupt_deltas(deltas, veil, self._rng)

        pre_l5_in = dict(deltas)
        deltas = pre_apply(self._ctx, signal, deltas)
        l5pre_snap = dict(deltas)
        override_fired = pre_l5_in != l5pre_snap

        apply_deltas(self.state, deltas, self.params)
        decay_step(
            self.state,
            self.params,
            decay_multiplier=self._entropy.decay_multiplier(),
            trait_prior=self._trait_prior,
        )
        excess = self._quasar.assess(self.state)
        self._quasar.apply_gravity(self.state, excess)

        post_apply(self._ctx, signal)
        due = tick_pending(self._ctx)
        if due:
            apply_deltas(self.state, due, self.params)

        if self.veil_machine is not None:
            self.veil_machine.advance()

        post_state = self.state.as_dict()
        for k in _VAR_STOCKS:
            d = post_state[k] - pre_state_for_var[k]
            hist = self._delta_history[k]
            hist.append(d)
            if len(hist) > VAR_WINDOW:
                del hist[0]
            if len(hist) >= 2:
                mean = sum(hist) / len(hist)
                var = sum((x - mean) ** 2 for x in hist) / (len(hist) - 1)
            else:
                var = 0.0
            setattr(self.state, f"{k}_var", var)

        neighbors_after: dict[str, dict[str, float]] | None = None
        if self.network is not None and pre_snapshot is not None:
            propagate(self.network, self.focal, pre_snapshot, self.state)
            neighbors_after = {
                n: self.network.agents[n].as_dict()
                for n in self.network.agents
                if n != self.focal
            }

        result = StepResult(
            session=self._session,
            signal=signal,
            l1_deltas=l1_snap,
            post_l5pre_deltas=l5pre_snap,
            post_l0_state=self.state.as_dict(),
            veil_state=veil.name if veil is not None else None,
            override_fired=override_fired,
            neighbors=neighbors_after,
        )
        self._session += 1
        self._history.append(result)
        if len(self._history) > self._history_max:
            del self._history[0]
        return result

    def history(self) -> list[dict[str, Any]]:
        return [
            {
                "session": r.session,
                "signal": r.signal,
                "l1_deltas": r.l1_deltas,
                "post_l5pre_deltas": r.post_l5pre_deltas,
                "post_l0_state": r.post_l0_state,
                "veil_state": r.veil_state,
                "override_fired": r.override_fired,
            }
            for r in self._history
        ]

    def memories(self) -> list[dict[str, Any]]:
        base_stocks = ("trust", "affection", "suspicion", "resistance")
        out: list[dict[str, Any]] = []
        prev_state: dict[str, float] | None = None
        for r in self._history:
            if prev_state is None:
                changes = {
                    k: v for k, v in r.post_l5pre_deltas.items() if k in base_stocks
                }
            else:
                changes = {
                    k: r.post_l0_state.get(k, 0.0) - prev_state.get(k, 0.0)
                    for k in base_stocks
                }
            prev_state = r.post_l0_state
            if not changes:
                summary = f"{r.signal}: no change"
            else:
                stock, val = max(changes.items(), key=lambda kv: abs(kv[1]))
                sign = "+" if val >= 0 else ""
                summary = f"{stock.capitalize()} {sign}{val:.1f} via {r.signal}"
            out.append({"session": r.session, "signal": r.signal, "summary": summary})
        return out[-10:]

    def missions(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for r in self._history:
            if not r.override_fired:
                continue
            diff = {
                k: r.post_l5pre_deltas.get(k, 0.0) - r.l1_deltas.get(k, 0.0)
                for k in set(r.post_l5pre_deltas) | set(r.l1_deltas)
            }
            diff = {k: v for k, v in diff.items() if abs(v) > 1e-9}
            if diff:
                stock, val = max(diff.items(), key=lambda kv: abs(kv[1]))
                sign = "+" if val >= 0 else ""
                summary = (
                    f"Override on '{r.signal}': {stock} {sign}{val:.2f} adjustment"
                )
            else:
                summary = f"Override fired on '{r.signal}'"
            out.append(
                {
                    "session": r.session,
                    "signal": r.signal,
                    "override_summary": summary,
                },
            )
        return out[-10:]

    def trends(self) -> dict[str, list[Any]]:
        stocks = ["trust", "affection", "suspicion", "resistance"]
        result: dict[str, list[Any]] = {k: [] for k in stocks}
        sessions: list[int] = []
        for r in self._history:
            sessions.append(r.session)
            for k in stocks:
                result[k].append(r.post_l0_state.get(k, 0.0))
        result["sessions"] = sessions
        return result

    def network_state(self) -> dict[str, Any]:
        if self.network is None:
            return {"focal": self.focal, "neighbors": {}}
        return {
            "focal": self.focal,
            "focal_state": self.state.as_dict(),
            "neighbors": {
                n: self.network.agents[n].as_dict()
                for n in self.network.agents
                if n != self.focal
            },
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "persona": self.persona.persona,
            "archetype": self.persona.archetype,
            "session": self._session,
            "state": self.state.as_dict(),
            "veil_state": self.veil_machine.current().name
            if self.veil_machine
            else None,
            "win": self.state.win_condition(),
        }
