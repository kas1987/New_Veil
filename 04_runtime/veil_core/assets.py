"""Helpers for loading narrative JSON assets with lightweight validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

_VEIL_ROOT = Path(__file__).resolve().parents[2] / ".20_Veil"
_DIALOGUE_PATH = _VEIL_ROOT / "dialogue" / "lyssandra_dialogue_templates.json"
_HERALD_PATH = _VEIL_ROOT / "Audio" / "herald_voice_profiles_81.json"
_PACKAGE_DIALOGUE = Path(__file__).resolve().parent / "data" / "lyssandra_dialogue_templates.sample.json"
_PACKAGE_HERALDS = Path(__file__).resolve().parent / "data" / "herald_voice_profiles.sample.json"


class AssetNotFoundError(FileNotFoundError):
    """Raised when expected narrative assets are missing from the checkout."""


def _load_json(path: Path) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def load_lyssandra_dialogue_templates() -> Dict[str, Any]:
    """Return the dialogue template structure used by the Lyssandra system."""

    data = _load_json(_DIALOGUE_PATH) or _load_json(_PACKAGE_DIALOGUE)
    if data is None:
        raise AssetNotFoundError("Lyssandra dialogue templates missing")
    _validate_dialogue_templates(data)
    return data


def load_herald_voice_profiles() -> Dict[str, Any]:
    """Return the full herald matrix definition (81 herald archetypes)."""

    data = _load_json(_HERALD_PATH) or _load_json(_PACKAGE_HERALDS)
    if data is None:
        raise AssetNotFoundError("Herald voice profiles missing")
    _validate_herald_profiles(data)
    return data


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def _validate_dialogue_templates(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Dialogue templates must be a mapping of persona -> config")

    required_persona_keys = {"persona_id", "base_mask", "cultural_mask"}
    required_dialogue_sections = {"tiers"}

    for persona, config in payload.items():
        if not isinstance(config, dict):
            raise ValueError(f"Persona {persona} must map to a dictionary")
        missing = required_persona_keys - config.keys()
        if missing:
            raise ValueError(f"Persona {persona} missing keys: {sorted(missing)}")

        dialogue = config.get("dialogue", {})
        if not isinstance(dialogue, dict):
            raise ValueError(f"Persona {persona} dialogue section must be mapping")
        if not required_dialogue_sections.issubset(dialogue.keys()):
            raise ValueError(f"Persona {persona} dialogue missing 'tiers' definition")

        tiers = dialogue["tiers"]
        if not isinstance(tiers, dict) or not tiers:
            raise ValueError(f"Persona {persona} tiers must be a non-empty mapping")
        for tier, entries in tiers.items():
            if not isinstance(entries, dict):
                raise ValueError(f"Persona {persona} tier {tier} must contain dict of dialogue types")
            for dtype, lines in entries.items():
                if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
                    raise ValueError(f"Persona {persona} tier {tier} dialogue '{dtype}' must be a list of strings")


def _validate_herald_profiles(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Herald profiles must be a mapping of herald_id -> metadata")

    for herald_id, profile in payload.items():
        if not isinstance(profile, dict):
            raise ValueError(f"Herald {herald_id} must map to a dictionary")
        for key in ("mind_voice", "body_voice", "binding_preferences"):
            if key not in profile:
                raise ValueError(f"Herald {herald_id} missing '{key}'")
        if not isinstance(profile["binding_preferences"], list):
            raise ValueError(f"Herald {herald_id} binding_preferences must be a list")


__all__ = [
    "AssetNotFoundError",
    "load_herald_voice_profiles",
    "load_lyssandra_dialogue_templates",
]
