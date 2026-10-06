"""MetaChromatic hero character catalog (PDR-0002).

Loads taxonomy-aligned character cards from seed JSON and optional
``13_agents/**/profile.json`` overlays.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
SEED_PATH = ROOT / "00_harness" / "04_metadata" / "hero_character_seed.json"
AGENTS_DIR = ROOT / "13_agents"
PERSONAS_PATH = ROOT / "04_runtime" / "dssm_engine" / "configs" / "personas.json"

PUBLIC_CARD_FIELDS = (
    "model_slug",
    "model_name",
    "character_name",
    "summary",
    "aurora_tier",
    "aurora_quadrant",
    "archetype",
    "emotional_archetype",
    "identity_tags",
    "visual_anchors",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _persona_by_agent(agent_id: str) -> dict[str, Any] | None:
    if not PERSONAS_PATH.exists():
        return None
    raw = _load_json(PERSONAS_PATH)
    agent_to_persona = {
        "mira": "Mira",
        "vael": "Shadow",
        "solenne": "Solenne",
        "archivist": "Elias",
        "witness": "Witness",
    }
    persona_name = agent_to_persona.get(agent_id)
    if not persona_name:
        return None
    for row in raw.get("personas", []):
        if row.get("persona") == persona_name:
            return row
    return None


def _overlay_profile(card: dict[str, Any], agent_id: str) -> dict[str, Any]:
    profile_path = AGENTS_DIR / agent_id / "profile.json"
    if not profile_path.exists():
        return card
    profile = _load_json(profile_path)
    merged = dict(card)
    merged["model_slug"] = agent_id
    merged["model_name"] = profile.get("display_name") or merged.get("model_name", agent_id)
    merged["character_name"] = profile.get("true_name") or profile.get("display_name") or merged.get("character_name")
    if profile.get("role"):
        merged["summary"] = profile["role"]
    traits = profile.get("traits") or []
    if traits and not merged.get("identity_tags"):
        merged["identity_tags"] = traits
    merged["source"] = str(profile_path.relative_to(ROOT)).replace("\\", "/")
    persona = _persona_by_agent(agent_id)
    if persona:
        merged["archetype"] = persona.get("archetype", merged.get("archetype"))
        merged["emotional_archetype"] = persona.get("attachment_state", merged.get("emotional_archetype"))
    return merged


def load_catalog(seed_path: Path | None = None, agents_dir: Path | None = None) -> list[dict[str, Any]]:
    seed_file = seed_path or SEED_PATH
    agents_root = agents_dir or AGENTS_DIR
    if not seed_file.exists():
        return []
    seed = _load_json(seed_file)
    cards: list[dict[str, Any]] = []
    for row in seed.get("characters", []):
        if not isinstance(row, dict):
            continue
        slug = str(row.get("model_slug", "")).strip()
        card = _overlay_profile(row, slug) if slug else dict(row)
        cards.append(card)
    discovered = {str(c.get("model_slug")) for c in cards}
    for agent_dir in sorted(agents_root.glob("*")):
        if not agent_dir.is_dir():
            continue
        agent_id = agent_dir.name
        if agent_id in discovered:
            continue
        profile_path = agent_dir / "profile.json"
        if not profile_path.exists():
            continue
        cards.append(
            _overlay_profile(
                {
                    "model_slug": agent_id,
                    "model_name": agent_id.title(),
                    "character_name": agent_id.title(),
                    "summary": "",
                    "source": str(profile_path.relative_to(ROOT)).replace("\\", "/"),
                },
                agent_id,
            )
        )
    return cards


def card_display_fields(card: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in PUBLIC_CARD_FIELDS:
        value = card.get(key)
        if value in (None, "", []):
            continue
        out[key] = value
    return out
