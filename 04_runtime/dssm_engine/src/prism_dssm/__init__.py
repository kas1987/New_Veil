"""Prism DSSM — Dynamic Social Systems Modeling, layered Veil engine.

Layered field-effect architecture:
    Input → L3 Veil → L1 Persona → L2 Attachment → L0 Core → L4 Network → L5 Override → State

The L0 core (`dssm_core`) is contamination-free: it imports nothing from the
other layers. Higher layers shape signals before/after L0 sees them.
"""

from .config_loader import load_config_dir
from .dssm_core import apply_deltas, decay_step, signal_gain
from .models import CoreParams, CoreState, OverrideContext, Signal, VeilState

__all__ = [
    "CoreParams",
    "CoreState",
    "OverrideContext",
    "Signal",
    "VeilState",
    "apply_deltas",
    "decay_step",
    "load_config_dir",
    "signal_gain",
]
