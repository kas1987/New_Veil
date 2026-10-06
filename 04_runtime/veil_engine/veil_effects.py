"""DSSM L3 - Veil Field Effects.

Three pipeline positions:
    L3a (pre-L0):   apply_veil(scalar) | corrupt(deltas)
    L3b (decay):    decay_multiplier()
    L3c (post-L0):  DarkQuasar.apply_gravity(state)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path as _Path

from .models import CoreState, VeilState


def apply_veil_scalar(
    raw_signal: float, avg_trust: float, avg_affection: float,
    veil: VeilState, rng: random.Random,
) -> float:
    s = raw_signal * veil.entropy_multiplier
    if veil.signal_noise > 0.0:
        s += rng.gauss(0.0, veil.signal_noise)
    if veil.quasar_active and avg_trust >= veil.trust_quasar_threshold:
        if rng.random() < veil.spike_probability:
            s *= veil.spike_intensity
            if rng.random() < veil.spike_flip_chance:
                s = -s
        if avg_affection >= veil.affection_instability_threshold and s < 0:
            s *= 1.25
    return s


def corrupt_deltas(
    deltas: dict[str, float], veil: VeilState, rng: random.Random,
    polarity_flip_chance: float = 0.0, dropout_chance: float = 0.0,
) -> dict[str, float]:
    if rng.random() < dropout_chance:
        return {}
    out: dict[str, float] = {}
    for k, v in deltas.items():
        if v == 0.0:
            out[k] = 0.0
            continue
        nv = v * max(0.0, 1.0 + rng.gauss(0.0, veil.signal_noise))
        if rng.random() < polarity_flip_chance:
            nv = -nv
        out[k] = nv
    return out


def maybe_force_spike(veil: VeilState, session_idx: int, period: int, intensity: float | None = None) -> float:
    if period <= 0 or session_idx <= 0 or session_idx % period != 0:
        return 0.0
    return -(intensity if intensity is not None else 6.0) * veil.entropy_multiplier


@dataclass
class EntropyConfig:
    veil_intensity: float = 1.0
    spike_probability: float = 0.05
    spike_magnitude: float = 2.5
    jitter_sigma: float = 0.05


class EntropyEngine:
    def __init__(self, config: EntropyConfig | None = None, rng: random.Random | None = None):
        self.config = config or EntropyConfig()
        self.rng = rng or random.Random()
        self.last_spike: bool = False

    def decay_multiplier(self) -> float:
        c = self.config
        spike = self.rng.random() < c.spike_probability
        self.last_spike = spike
        m = c.veil_intensity * (c.spike_magnitude if spike else 1.0)
        m *= max(0.0, 1.0 + self.rng.gauss(0.0, c.jitter_sigma))
        return m


@dataclass
class QuasarConfig:
    affection_instability_threshold: float = 70.0
    trust_instability_threshold: float = 60.0
    spike_boost_per_excess: float = 0.01
    spike_boost_cap: float = 0.20
    suspicion_pull: float = 0.15
    affection_drag: float = 0.05
    resistance_dissolve: float = 0.02
    severity_boost_per_excess: float = 0.02


class DarkQuasar:
    def __init__(self, config: QuasarConfig | None = None, rng: random.Random | None = None):
        self.config = config or QuasarConfig()
        self.rng = rng or random.Random()
        self.active: bool = False
        self.last_excess: float = 0.0

    def assess(self, state: CoreState) -> float:
        c = self.config
        trust_excess = max(0.0, state.trust - c.trust_instability_threshold)
        aff_excess = max(0.0, state.affection - c.affection_instability_threshold)
        excess = trust_excess + 0.5 * aff_excess
        self.active = excess > 0.0
        self.last_excess = excess
        return excess

    def spike_probability_boost(self, excess: float) -> float:
        return min(self.config.spike_boost_cap, self.config.spike_boost_per_excess * excess)

    def severity_multiplier(self, excess: float) -> float:
        return 1.0 + self.config.severity_boost_per_excess * excess

    def apply_gravity(self, state: CoreState, excess: float) -> None:
        if excess <= 0.0:
            return
        c = self.config
        drag_scale = min(1.0, excess / 30.0)
        state.suspicion += c.suspicion_pull * drag_scale
        state.affection -= c.affection_drag * drag_scale
        if state.trust > c.trust_instability_threshold:
            state.resistance -= c.resistance_dissolve * (state.trust / 100.0)
        state.clamp()


class VeilStateMachine:
    def __init__(self, states: list[VeilState], schedule: list[str] | None = None):
        self.states: dict[str, VeilState] = {s.name: s for s in states}
        self.schedule: list[str] = schedule or [s.name for s in states]
        self.tick: int = 0

    @classmethod
    def from_config(cls, path: _Path | str) -> VeilStateMachine:
        data = json.loads(_Path(path).read_text(encoding="utf-8"))
        states = [_veil_from_dict(d) for d in data["states"]]
        return cls(states, data.get("schedule"))

    def current(self) -> VeilState:
        return self.states[self.schedule[self.tick % len(self.schedule)]]

    def advance(self) -> None:
        self.tick += 1

    def override_intensity(self, multiplier: float) -> None:
        for s in self.states.values():
            s.entropy_multiplier *= multiplier


def _veil_from_dict(d: dict) -> VeilState:
    return VeilState(
        name=d.get("veil_state", d.get("name", "calm")),
        entropy_multiplier=float(d.get("entropy_multiplier", 1.0)),
        signal_noise=float(d.get("signal_noise", 0.0)),
        quasar_active=bool(d.get("quasar_active", d.get("veil_state") == "quasar_active")),
        spike_probability=float(d.get("spike_probability", 0.05)),
        spike_intensity=float(d.get("spike_intensity", 1.5)),
        spike_flip_chance=float(d.get("spike_flip_chance", 0.25)),
        affection_instability_threshold=float(d.get("affection_instability_threshold", 70.0)),
        trust_quasar_threshold=float(d.get("trust_quasar_threshold", 55.0)),
    )
