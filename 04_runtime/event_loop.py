"""Event loop — the main runtime cycle for Veil Town.

Pattern: observe → decide → act → validate → log → repeat
Each tick advances the Veil state machine, processes pending tasks,
applies alignment checks, and logs everything to replay.
"""

from __future__ import annotations

from veil_loader import load_module

# Lazy imports — loaded at runtime to avoid circular deps
_memory = None
_alignment = None
_veil = None


def _load_modules():
    global _memory, _alignment, _veil
    if _memory is None:
        _memory = load_module("memory_router", "03_memory/memory_router.py")
    if _veil is None:
        _veil = load_module("veil_engine", "04_runtime/veil_engine/__init__.py")
