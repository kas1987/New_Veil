"""Veil Engine — DSSM L3 field effects for Viel Small Town.

Three pipeline positions:
    L3a (pre-L0):   apply_veil_scalar() | corrupt_deltas()  — distort incoming signal
    L3b (decay):    EntropyEngine.decay_multiplier()        — entropy speeds/slows decay
    L3c (post-L0):  DarkQuasar.apply_gravity()             — emotional-gravity drag
"""

from .models import CoreState, Signal, VeilState
from .veil_effects import (
    DarkQuasar,
    EntropyConfig,
    EntropyEngine,
    QuasarConfig,
    VeilStateMachine,
    apply_veil_scalar,
    corrupt_deltas,
    maybe_force_spike,
)

__all__ = [
    "CoreState",
    "Signal",
    "VeilState",
    "apply_veil_scalar",
    "corrupt_deltas",
    "maybe_force_spike",
    "EntropyConfig",
    "EntropyEngine",
    "QuasarConfig",
    "DarkQuasar",
    "VeilStateMachine",
]
