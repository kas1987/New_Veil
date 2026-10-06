"""Tests for prism_dssm.sensitivity."""

from __future__ import annotations

from dataclasses import fields as dc_fields
from pathlib import Path

from prism_dssm.models import CoreParams
from prism_dssm.sensitivity import sensitivity_report

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


def _float_field_names() -> list[str]:
    out: list[str] = []
    for f in dc_fields(CoreParams):
        t = f.type
        if t is float or t == "float":
            out.append(f.name)
    return out


def test_sensitivity_report_smoke():
    out = sensitivity_report(
        CONFIG_DIR,
        fields=["trust_decay", "resistance_decay"],
        delta_pct=0.10,
        sessions=5,
        ratios=(5.0,),
        seeds=(11,),
        target_persona="Mira",
    )
    assert "baseline_win_rate" in out
    assert 0.0 <= out["baseline_win_rate"] <= 1.0
    assert out["delta_pct"] == 0.10
    assert isinstance(out["fields"], list)
    assert len(out["fields"]) == 2
    required = {
        "field",
        "baseline_value",
        "plus_value",
        "plus_win_rate",
        "minus_value",
        "minus_win_rate",
        "sensitivity",
    }
    for entry in out["fields"]:
        assert required <= set(entry.keys())
        assert 0.0 <= entry["plus_win_rate"] <= 1.0
        assert 0.0 <= entry["minus_win_rate"] <= 1.0


def test_sensitivity_default_fields_includes_all_floats():
    out = sensitivity_report(
        CONFIG_DIR,
        fields=None,
        delta_pct=0.10,
        sessions=3,
        ratios=(5.0,),
        seeds=(11,),
        target_persona="Mira",
    )
    reported = {e["field"] for e in out["fields"]}
    expected = set(_float_field_names())
    assert reported == expected
