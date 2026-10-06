"""Unified data models for the Veil Engine.

CoreState is now compatible with the DSSM engine's 4-stock model.
The 3-field constructor still works (resistance defaults to 70.0, variance to 0.0).
The 4-field or 8-field constructor also works (resistance and variance are optional).
These fields bridge the gap between the town's veil_engine and the full DSSM engine.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class CoreState:
    """Emotional state consumed by the Dark Quasar gravity model.

    Compatible with prism_dssm.models.CoreState (4 stock fields + 4 variance fields).
    The 3-field constructor (trust, affection, suspicion) still works and
    defaults resistance=70.0 and all variances to 0.0.
    """

    trust: float = 30.0
    affection: float = 25.0
    suspicion: float = 10.0
    resistance: float = 70.0

    # Variance fields (for DSSM compatibility)
    trust_var: float = 0.0
    affection_var: float = 0.0
    suspicion_var: float = 0.0
    resistance_var: float = 0.0

    def clamp(self, lo: float = 0.0, hi: float = 100.0) -> None:
        self.trust = max(lo, min(hi, self.trust))
        self.affection = max(lo, min(hi, self.affection))
        self.suspicion = max(lo, min(hi, self.suspicion))
        self.resistance = max(lo, min(hi, self.resistance))

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def win_condition(self) -> bool:
        """L0 win condition: trust > 60, suspicion < 40, resistance < 35."""
        return self.trust > 60.0 and self.suspicion < 40.0 and self.resistance < 35.0

    @classmethod
    def from_3field(cls, trust: float = 50.0, affection: float = 50.0, suspicion: float = 10.0) -> CoreState:
        """Construct from the old 3-field interface with sensible defaults."""
        return cls(trust=trust, affection=affection, suspicion=suspicion)


@dataclass
class VeilState:
    """A named Veil field configuration.

    Governs signal distortion, entropy, spike probability, and emotional
    gravity thresholds in the Dark Quasar layer.
    """

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
class Signal:
    """Per-stock delta vector. Same shape as DSSM Signal."""

    trust_delta: float = 0.0
    affection_delta: float = 0.0
    suspicion_delta: float = 0.0
    resistance_delta: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "trust": self.trust_delta,
            "affection": self.affection_delta,
            "suspicion": self.suspicion_delta,
            "resistance": self.resistance_delta,
        }
