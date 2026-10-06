"""Tests for the alignment scoring engine and quarantine system."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from veil_loader import load_module

_HERE = Path(__file__).resolve().parent.parent
scorer = load_module("alignment_scorer", _HERE / "scorer.py")
quarantine_mod = load_module("alignment_quarantine", _HERE / "quarantine.py")


def test_alignment_gate_passes_with_canon_refs():
    score = scorer.score_text(
        "warm prism hidden quasar truth memory resonance",
        role_keywords=[],
        canon_refs=["VEIL-001"],
    )
    assert score.pass_gate is True


def test_alignment_gate_fails_without_canon():
    score = scorer.score_text(
        "random nonsense without any keywords",
        role_keywords=["mira"],
        canon_refs=[],
    )
    assert score.canon_fidelity < 0.75 or score.role_fidelity < 0.70


def test_drift_risk_high_without_refs():
    score = scorer.score_text("anything", canon_refs=[])
    assert score.drift_risk > 0.3


def test_prism_resonance_keywords():
    score = scorer.score_text("warm beautiful guide light prism", canon_refs=["VEIL-001"])
    assert score.prism_resonance > 0.5


def test_quasar_resonance_keywords():
    score = scorer.score_text("gravity hidden truth danger quasar depth", canon_refs=["VEIL-002"])
    assert score.dark_quasar_resonance > 0.5


def test_should_quarantine_low_canon():
    alignment = {"canon_fidelity": 0.5, "drift_risk": 0.4, "role_fidelity": 0.8}
    should, reason = quarantine_mod.should_quarantine(alignment)
    assert should is True
    assert "canon_fidelity" in reason


def test_should_quarantine_high_drift():
    alignment = {"canon_fidelity": 0.9, "drift_risk": 0.5, "role_fidelity": 0.9}
    should, reason = quarantine_mod.should_quarantine(alignment)
    assert should is True
    assert "drift_risk" in reason


def test_should_not_quarantine_good_alignment():
    alignment = {"canon_fidelity": 0.9, "drift_risk": 0.2, "role_fidelity": 0.95}
    should, reason = quarantine_mod.should_quarantine(alignment)
    assert should is False


def test_should_quarantine_quasar_elevated_drift():
    alignment = {"canon_fidelity": 0.85, "drift_risk": 0.30, "role_fidelity": 0.80}
    should, reason = quarantine_mod.should_quarantine(alignment, veil_state="quasar_active")
    assert should is True
    assert "quasar_active" in reason


def test_emotional_depth_keywords():
    score = scorer.score_text("memory emotion symbol resonance dream", canon_refs=["VEIL-003"])
    assert score.emotional_depth > 0.5


def test_role_fidelity_with_keywords():
    score = scorer.score_text("mira offers guidance", role_keywords=["mira"], canon_refs=["MIRA-001"])
    assert score.role_fidelity > 0.5
