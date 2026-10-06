"""Shared dataclasses across the DSSM engine.

Single source of truth for stock state, signal shape, veil state, override context.
Imported by every layer module.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field
from typing import Any

CLAMP_LO = 0.0
CLAMP_HI = 100.0


def clamp(x: float) -> float:
    if x < CLAMP_LO:
        return CLAMP_LO
    if x > CLAMP_HI:
        return CLAMP_HI
    return x


@dataclass
class CoreParams:
    """L0 physical constants. Pure physics — no character voice."""

    trust_decay: float = 0.012
    affection_decay: float = 0.015
    suspicion_decay: float = 0.020
    resistance_decay: float = 0.008

    trust_baseline: float = 30.0
    affection_baseline: float = 25.0
    suspicion_baseline: float = 20.0
    resistance_baseline: float = 0.0

    resistance_gate: float = 0.6
    trust_release_threshold: float = 50.0
    trust_dissolve_k: float = 0.025

    prior_shrinkage_rate: float = 1.0


@dataclass
class CoreState:
    """L0 stocks for a single agent. Bounded to [0, 100]."""

    trust: float = 30.0
    affection: float = 25.0
    suspicion: float = 50.0
    resistance: float = 70.0

    trust_var: float = 0.0
    affection_var: float = 0.0
    suspicion_var: float = 0.0
    resistance_var: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def clamp(self) -> None:
        self.trust = clamp(self.trust)
        self.affection = clamp(self.affection)
        self.suspicion = clamp(self.suspicion)
        self.resistance = clamp(self.resistance)

    def win_condition(self) -> bool:
        return self.trust > 60.0 and self.suspicion < 40.0 and self.resistance < 35.0


# Path-A compatibility alias (Path A used StockState).
StockState = CoreState


@dataclass
class Signal:
    """Per-stock delta vector. Output of L1/L2/L5 layers, input to L0.apply_deltas."""

    trust_delta: float = 0.0
    affection_delta: float = 0.0
    suspicion_delta: float = 0.0
    resistance_delta: float = 0.0

    @classmethod
    def from_dict(cls, d: dict[str, float]) -> Signal:
        return cls(
            trust_delta=float(d.get("trust", 0.0)),
            affection_delta=float(d.get("affection", 0.0)),
            suspicion_delta=float(d.get("suspicion", 0.0)),
            resistance_delta=float(d.get("resistance", 0.0)),
        )

    def to_dict(self) -> dict[str, float]:
        return {
            "trust": self.trust_delta,
            "affection": self.affection_delta,
            "suspicion": self.suspicion_delta,
            "resistance": self.resistance_delta,
        }


@dataclass
class VeilState:
    """L3 veil parameters. Loaded from configs/veil_states.json."""

    name: str = "calm"
    entropy_multiplier: float = 1.0
    signal_noise: float = 0.0
    quasar_active: bool = False
    spike_probability: float = 0.05
    spike_intensity: float = 1.5
    spike_flip_chance: float = 0.25
    affection_instability_threshold: float = 70.0
    trust_quasar_threshold: float = 55.0


@dataclass
class OverrideContext:
    """L5 narrative-override scratch space, one per persona."""

    persona: str
    rules: list[dict[str, Any]]
    history: deque[tuple[str, int]] = field(default_factory=lambda: deque(maxlen=10))
    pending: list[tuple[int, dict[str, float]]] = field(default_factory=list)
    counters: dict[str, int] = field(default_factory=dict)
