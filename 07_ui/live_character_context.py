"""Live character context helpers (PDR-0004) — no Gradio dependency."""

from __future__ import annotations

import sys
from pathlib import Path

_UI_ROOT = Path(__file__).resolve().parent
if str(_UI_ROOT) not in sys.path:
    sys.path.insert(0, str(_UI_ROOT))

from hero.character_catalog import load_catalog
from observatory.data import read_agent_player_relationship, read_memories


def format_presence(agent_id: str) -> str:
    cards = {c.get("model_slug"): c for c in load_catalog()}
    card = cards.get(agent_id, {})
    name = card.get("character_name") or card.get("model_name") or agent_id
    summary = card.get("summary") or "No summary available."
    archetype = card.get("archetype") or "—"
    emotional = card.get("emotional_archetype") or "—"
    tags = ", ".join(card.get("identity_tags") or []) or "—"
    return (
        f"### {name}\n"
        f"**slug:** `{agent_id}` · **archetype:** `{archetype}` · **emotional_archetype:** `{emotional}`\n\n"
        f"{summary}\n\n"
        f"**identity_tags:** {tags}"
    )


def suggested_prompts(agent_id: str) -> str:
    prompts = {
        "mira": "Ask what she remembers · Wait in silence · Acknowledge her mood",
        "vael": "Ask for an honest mirror · Refuse an easy answer · Name your fear",
        "solenne": "Offer patience · Ask about protection · Share something vulnerable",
        "archivist": "Ask what was recorded · Request a pattern · Sit quietly",
        "witness": "Observe without demanding · Ask what was seen before",
    }
    items = prompts.get(agent_id, "Speak freely · Notice the room · Ask a deeper question")
    return f"**Suggested branch prompts:** {items}"


def refresh_live_context(agent_id: str) -> tuple[str, dict, list[list], str]:
    telemetry = read_agent_player_relationship(agent_id)
    memories = read_memories(agent_id=agent_id, limit=8)
    return (
        format_presence(agent_id),
        telemetry,
        memories,
        suggested_prompts(agent_id),
    )
