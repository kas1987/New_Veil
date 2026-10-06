"""DSSM L1 (Persona) + L2 (Attachment).

L1 — Persona Filter: maps a raw signal name to a per-stock delta dict, scoped per persona.
L2 — Attachment Modifier: scales those deltas by anxious/avoidant/secure profile.

JSON-driven. Adding a Sister is a single `personas.json` entry — no code change.
Source: Path B canonical L1/L2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# L1 — Persona Filter
# ---------------------------------------------------------------------------


@dataclass
class PersonaConfig:
    persona: str
    raw: dict[str, Any]

    @property
    def archetype(self) -> str:
        return self.raw.get("archetype", "")

    @property
    def signal_weights(self) -> dict[str, dict[str, float]]:
        return self.raw.get("signal_weights", {})

    @property
    def attachment_state(self) -> str:
        return self.raw.get("attachment_state", "secure")

    @property
    def attachment_modifiers(self) -> dict[str, float]:
        return self.raw.get("attachment_modifiers", {})

    @property
    def override_rules(self) -> list[dict[str, Any]]:
        return self.raw.get("override_rules", [])

    @property
    def initial_state(self) -> dict[str, float]:
        return self.raw.get("initial_state", {})

    @property
    def trait_prior(self) -> dict[str, float]:
        return self.raw.get("trait_prior", {})


def load_persona(path: str | Path) -> PersonaConfig:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return PersonaConfig(persona=raw["persona"], raw=raw)


def load_personas(path: str | Path) -> dict[str, PersonaConfig]:
    """Load `configs/personas.json` (a list under key `personas`)."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        p["persona"]: PersonaConfig(persona=p["persona"], raw=p)
        for p in raw["personas"]
    }


def filter_signal(persona: PersonaConfig, signal: str) -> dict[str, float]:
    """Return per-stock deltas for `signal` under this persona. Unknown → empty dict."""
    mapping = persona.signal_weights.get(signal)
    return {} if mapping is None else {k: float(v) for k, v in mapping.items()}


# ---------------------------------------------------------------------------
# L2 — Attachment Modifier
# ---------------------------------------------------------------------------

POSITIVE_STOCKS = {"trust", "affection"}
NEGATIVE_STOCKS = {"suspicion", "resistance"}

DEFAULT_PROFILES: dict[str, dict[str, float]] = {
    "anxious": {
        "positive_gain_mult": 1.25,
        "positive_loss_mult": 1.40,
        "negative_gain_mult": 1.30,
        "negative_loss_mult": 1.10,
    },
    "avoidant": {
        "positive_gain_mult": 0.70,
        "positive_loss_mult": 1.15,
        "negative_gain_mult": 1.20,
        "negative_loss_mult": 0.85,
    },
    "secure": {
        "positive_gain_mult": 1.00,
        "positive_loss_mult": 1.00,
        "negative_gain_mult": 1.00,
        "negative_loss_mult": 1.00,
    },
}


def apply_attachment(
    deltas: dict[str, float],
    attachment_state: str,
    overrides: dict[str, float] | None = None,
) -> dict[str, float]:
    profile = dict(DEFAULT_PROFILES.get(attachment_state, DEFAULT_PROFILES["secure"]))
    if overrides:
        profile.update(overrides)

    out: dict[str, float] = {}
    for stock, value in deltas.items():
        if stock in POSITIVE_STOCKS:
            mult = (
                profile["positive_gain_mult"]
                if value >= 0
                else profile["positive_loss_mult"]
            )
        elif stock in NEGATIVE_STOCKS:
            mult = (
                profile["negative_gain_mult"]
                if value >= 0
                else profile["negative_loss_mult"]
            )
        else:
            mult = 1.0
        out[stock] = value * mult
    return out
