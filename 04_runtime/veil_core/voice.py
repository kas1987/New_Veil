"""Lyssandra voice integration helpers."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Dict, Optional

import requests

from . import assets
from .prism import SisterFacet, SisterPrismSystem

logger = logging.getLogger(__name__)


class LyssandraVoiceIntegration:
    """Thin wrapper that pairs prism state with dialogue + VoiceApp calls."""

    def __init__(
        self,
        *,
        voiceapp_base_url: str = "http://localhost:8000/api/v1",
        dialogue_templates: Optional[Dict[str, Dict]] = None,
    ) -> None:
        self.voiceapp_base_url = voiceapp_base_url.rstrip("/")
        self.dialogue_templates = dialogue_templates or assets.load_lyssandra_dialogue_templates()
        self.prism = SisterPrismSystem()

    # ------------------------------------------------------------------
    # Dialogue helpers
    # ------------------------------------------------------------------
    def select_persona(self, mirror_state: int, cultural_mask: str) -> Dict[str, str]:
        from .db import get_mock_persona  # local import to avoid circular deps

        persona = get_mock_persona(mirror_state, cultural_mask)
        template = self.dialogue_templates.get(persona["persona_id"])
        if not template:
            raise ValueError(f"No dialogue template for persona {persona['persona_id']}")
        return template

    def pick_dialogue_line(self, persona_template: Dict[str, Dict], tier: str, dialogue_type: str) -> str:
        tiers = persona_template.get("dialogue", {}).get("tiers", {})
        options = tiers.get(str(tier), {}).get(dialogue_type, [])
        if not options:
            raise ValueError(f"No dialogue available for tier {tier} ({dialogue_type})")
        return random.choice(options)

    # ------------------------------------------------------------------
    # Voice synthesis
    # ------------------------------------------------------------------
    def synthesize(self, *, mind_text: str, body_text: str, mind_voice: str, body_voice: str) -> requests.Response:
        payload = {
            "mind": {"text": mind_text, "voice": mind_voice},
            "body": {"text": body_text, "voice": body_voice},
        }
        url = f"{self.voiceapp_base_url}/voice/speak"
        logger.debug("POST %s", url)
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        return response


__all__ = ["LyssandraVoiceIntegration"]
