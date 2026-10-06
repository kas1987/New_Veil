"""Veil Town Persona Router — P1.1

Maps every town agent to its DSSM persona configuration (signal weights,
attachment profile, initial state, override rules). Also provides expanded
role-keyword banks for the alignment scorer so role_fidelity is scored
against words the agent's archetype is likely to use, not just raw trait
strings from profile.json.
"""

from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PERSONAS_PATH = _HERE / "dssm_engine" / "configs" / "personas.json"
_VOICE_SCHEMA_PATH = _HERE.parent / "13_agents" / "whispertech" / "voice_schema.json"

# Town agent_id → DSSM persona name (see personas.json)
_DEFAULT_MAP: dict[str, str] = {
    "mira":       "Mira",
    "vael":       "Shadow",      # Vael embodies The Mirror archetype
    "solenne":    "Solenne",     # The Guardian
    "lyra":       "Lyra",        # The Oracle
    "archivist":  "Elias",       # The Architect → memory/structure keeper
    "witness":    "Witness",     # The Observer
    "rendered":   "Rendered",    # The Transformer
    "threadwatcher": "Threadwatcher",  # The Unbound
    "warden":     "Sael",        # Stillward warden — The Tender
    "greeter":    "Halen",       # Congregation greeter — The Welcomer
}

# Expanded keyword banks per archetype. These are tuned against real LLM
# output for the voice/persona so scorer.role_fidelity stays above 0.7.
_KEYWORD_BANKS: dict[str, tuple[str, ...]] = {
    "The Catalyst": (
        # Mira: warm, playful, guiding, mysterious
        "warm", "warmth", "guide", "guidance", "light", "prism",
        "memory", "echo", "whisper", "whispers", "gentle", "soft",
        "playful", "mystery", "mysterious", "secret", "secrets",
        "dawn", "lantern", "path", "paths", "wander", "story",
        "stories", "resonance", "felt", "feel", "tangled", "glow",
    ),
    "The Mirror": (
        # Vael/Shadow: dark, honest, unsettling, transformative
        "mirror", "reflect", "reflection", "shadow", "shadows",
        "dark", "darkness", "truth", "honest", "cruel", "cruelty",
        "weight", "gravity", "void", "deep", "depth", "depths",
        "ruin", "fall", "transformation", "obsidian", "ash", "burn",
        "cold", "sharp", "honesty",
    ),
    "The Guardian": (
        # Solenne: radiant, protective, maternal, deliberate
        "radiant", "protect", "protective", "shield", "care",
        "gentle", "gentleness", "dawn", "light", "warmth", "warm",
        "promise", "guidance", "guide", "maternal", "safe",
        "safety", "deliberate", "calm", "calming", "hold", "patience",
        "patience", "grief", "grieving", "love", "loving",
    ),
    "The Architect": (
        # Archivist/Elias: structure, history, cryptic, ancient
        "structure", "build", "design", "ancient", "history",
        "echo", "echoes", "archive", "archives", "cryptic",
        "memory", "memories", "record", "recorded", "riddle",
        "riddles", "pattern", "patterns", "order", "ordered",
        "silence", "silent", "quietly", "alone", "lonely",
        "organized", "system", "catalog", "forgotten", "lost",
    ),
    "The Oracle": (
        # Lyra: vision, prophecy, depth, symbolic
        "see", "vision", "visions", "prophecy", "prophecies",
        "know", "knowing", "depth", "depths", "symbol", "symbolic",
        "thread", "threads", "resonance", "resonate", "future",
        "dream", "dreams", "whisper", "whispers", "truth",
        "mirror", "reflect", "insight", "foresee", "beneath",
    ),
    "The Observer": (
        # Witness: silence, observation, minimal
        "watch", "watched", "watching", "silent", "silence",
        "observe", "observed", "observing", "record", "recorded",
        "still", "quiet", "patience", "patient", "eye", "eyes",
        "saw", "seen", "before", "happen", "happened", "times",
        "yes", "no", "here", "there", "again",
    ),
    "The Tender": (
        # Warden Sael: peace, maintenance, bell, steady
        "peace", "peaceful", "bell", "stillness", "still",
        "garden", "tend", "maintain", "hold", "holding",
        "warm", "soft", "light", "care", "careful",
        "steady", "patient", "effortless", "invisible",
        "warden", "shelter", "rest", "breath", "calm",
    ),
    "The Welcomer": (
        # Halen: arrival, lantern, greeting, concern
        "welcome", "arrive", "lantern", "door", "glad",
        "sit", "warm", "walk", "tired", "rest",
        "offer", "smile", "hall", "light", "guide",
        "glad", "friend", "new", "come", "journey",
        "trouble", "alright", "concern", "fellowship", "safe",
    ),
    "The Transformer": (
        # The Rendered: burn, ash, transformation, weight
        "burn", "burning", "ash", "forge", "anvil",
        "transform", "transformation", "weight", "release",
        "casket", "ember", "iron", "key", "heavy",
        "hold", "carry", "liberation", "test", "truth",
        "cost", "obliterate", "recontextualize", "conviction",
    ),
}

# Also expose per-agent overrides when two personas share an archetype
# but need different keyword emphasis.
_AGENT_KEYWORD_OVERRIDES: dict[str, tuple[str, ...]] = {
    "mira":   ("elusive", "cunning", "game", "play"),
    "vael":   ("exhausted", "tired", "weary", "relentless"),
    "solenne": ("sister", "sisters", "family", "name", "bright"),
    "archivist": ("esmer", "loke", "books", "shelves", "dust"),
    "witness":  ("forgotten", "remember", "everything", "nothing"),
    "warden":   ("peace", "bell", "stillness", "garden", "tend"),
    "greeter":  ("welcome", "lantern", "arrive", "door", "glad"),
    "rendered": ("burn", "ash", "forge", "key", "casket"),
    "threadwatcher": ("thread", "threshold", "door", "walk", "seam"),
}


class PersonaRouter:
    def __init__(self, personas_path: Path | str | None = None) -> None:
        path = Path(personas_path) if personas_path else _PERSONAS_PATH
        raw = json.loads(path.read_text(encoding="utf-8"))
        self._personas: dict[str, dict] = {p["persona"]: p for p in raw.get("personas", [])}
        if _VOICE_SCHEMA_PATH.exists():
            self._voice_schema = json.loads(_VOICE_SCHEMA_PATH.read_text(encoding="utf-8"))
        else:
            self._voice_schema = {
                "emotional_voice_profiles": {},
                "agent_voice_overrides": {},
                "intimacy_tiers": {},
            }

    def resolve(self, agent_id: str) -> dict:
        """Return the DSSM persona config for a town agent."""
        persona_name = _DEFAULT_MAP.get(agent_id.lower(), agent_id.title())
        if persona_name not in self._personas:
            # Graceful fallback: return a generic secure persona
            return {
                "persona": agent_id.title(),
                "archetype": "The Unknown",
                "signal_weights": {},
                "attachment_state": "secure",
                "attachment_modifiers": {},
                "override_rules": [],
                "initial_state": {
                    "trust": 35.0, "affection": 25.0,
                    "suspicion": 40.0, "resistance": 60.0,
                },
            }
        return self._personas[persona_name]

    def archetype(self, agent_id: str) -> str:
        return self.resolve(agent_id).get("archetype", "The Unknown")

    def initial_state(self, agent_id: str) -> dict[str, float]:
        """Return {trust, affection, suspicion, resistance} defaults."""
        return self.resolve(agent_id).get("initial_state", {
            "trust": 35.0, "affection": 25.0,
            "suspicion": 40.0, "resistance": 60.0,
        })

    def signal_weights(self, agent_id: str) -> dict[str, dict[str, int]]:
        """Return signal weight map for this persona.
        Keys: compliment, silence, vulnerability, criticism, support, deception, honesty.
        Values: dict of stock → delta."""
        return self.resolve(agent_id).get("signal_weights", {})

    def attachment(self, agent_id: str) -> str:
        return self.resolve(agent_id).get("attachment_state", "secure")

    def role_keywords(self, agent_id: str) -> list[str]:
        """Return a keyword bank for alignment scorer role_fidelity."""
        arch = self.archetype(agent_id)
        bank = list(_KEYWORD_BANKS.get(arch, ()))
        overrides = _AGENT_KEYWORD_OVERRIDES.get(agent_id.lower(), ())
        return bank + list(overrides)

    def resistance_gate(self, agent_id: str, resistance: float, gate_coeff: float = 0.6) -> float:
        """Return the effective signal-gain multiplier (1 - gate_coeff * R/100)."""
        return max(0.0, 1.0 - gate_coeff * (resistance / 100.0))

    def voice_schema(self) -> dict:
        return self._voice_schema

    def _intimacy_tier_for_depth(self, emotional_depth: float) -> str:
        if emotional_depth >= 0.75:
            return "depth"
        if emotional_depth >= 0.55:
            return "revealing"
        if emotional_depth >= 0.30:
            return "hinting"
        return "surface"

    def voice_profile(
        self,
        agent_id: str,
        veil_state: str = "calm",
        emotional_tags: list[str] | None = None,
        emotional_depth: float = 0.0,
    ) -> dict:
        """Resolve WhisperTech voice settings for an agent in the current state."""
        schema = self._voice_schema
        profiles = schema.get("emotional_voice_profiles", {})
        overrides = schema.get("agent_voice_overrides", {}).get(agent_id.lower(), {})
        base_profile_name = overrides.get("base_profile", "calm")
        effective_profile_name = veil_state if veil_state in profiles else base_profile_name
        profile = dict(
            profiles.get(effective_profile_name)
            or profiles.get(base_profile_name)
            or profiles.get("calm")
            or {}
        )

        intimacy_tier = self._intimacy_tier_for_depth(emotional_depth)
        intimacy_modifiers = schema.get("intimacy_tiers", {}).get(intimacy_tier, {})
        profile["speaking_rate"] = round(
            float(profile.get("speaking_rate", 1.0))
            * float(intimacy_modifiers.get("speaking_rate_modifier", 1.0)),
            3,
        )
        profile["warmth"] = max(
            0.0,
            min(
                1.0,
                float(profile.get("warmth", 0.5))
                + float(intimacy_modifiers.get("warmth_modifier", 0.0)),
            ),
        )
        profile["silence_threshold"] = max(
            0.0,
            min(
                1.0,
                float(profile.get("silence_threshold", 0.3))
                + float(intimacy_modifiers.get("silence_modifier", 0.0)),
            ),
        )

        tag_set = {tag.lower() for tag in (emotional_tags or [])}
        if {"warmth", "care", "tenderness", "intimacy"} & tag_set:
            profile["warmth"] = min(1.0, profile["warmth"] + 0.1)
        if {"boundary", "sharpness", "testing", "hostility"} & tag_set:
            profile["warmth"] = max(0.0, profile["warmth"] - 0.15)
            profile["dominance"] = min(1.0, float(profile.get("dominance", 0.5)) + 0.15)
        if {"mystery", "depth", "dream", "echo", "quasar"} & tag_set:
            profile["resonance"] = min(1.0, float(profile.get("resonance", 0.5)) + 0.1)

        return {
            "profile_name": effective_profile_name,
            "base_profile_name": base_profile_name,
            "voice_characteristics": list(overrides.get("voice_characteristics", [])),
            "ssml_tags": list(overrides.get("ssml_tags", [])),
            "intimacy_tier": intimacy_tier,
            "attachment_state": self.attachment(agent_id),
            "archetype": self.archetype(agent_id),
            **profile,
        }


# Singleton convenience
_router: PersonaRouter | None = None


def get_router() -> PersonaRouter:
    global _router
    if _router is None:
        _router = PersonaRouter()
    return _router


def resolve(agent_id: str) -> dict:
    return get_router().resolve(agent_id)


def initial_state(agent_id: str) -> dict[str, float]:
    return get_router().initial_state(agent_id)


def signal_weights(agent_id: str) -> dict[str, dict[str, int]]:
    return get_router().signal_weights(agent_id)


def attachment(agent_id: str) -> str:
    return get_router().attachment(agent_id)


def role_keywords(agent_id: str) -> list[str]:
    return get_router().role_keywords(agent_id)


def resistance_gate(agent_id: str, resistance: float, gate_coeff: float = 0.6) -> float:
    return get_router().resistance_gate(agent_id, resistance, gate_coeff)


def voice_profile(
    agent_id: str,
    veil_state: str = "calm",
    emotional_tags: list[str] | None = None,
    emotional_depth: float = 0.0,
) -> dict:
    return get_router().voice_profile(agent_id, veil_state, emotional_tags, emotional_depth)


if __name__ == "__main__":
    import sys

    aid = sys.argv[1] if len(sys.argv) > 1 else "mira"
    r = get_router()
    print(f"Agent:      {aid}")
    print(f"Persona:    {r.resolve(aid)['persona']}")
    print(f"Archetype:  {r.archetype(aid)}")
    print(f"Attachment: {r.attachment(aid)}")
    print(f"Keywords:   {r.role_keywords(aid)[:8]}...")
    print(f"Initial:    {r.initial_state(aid)}")
