"""Alignment scorer — lexical signal extraction for runtime gating.

Keyword sets are tuned for natural atmospheric prose, not just exact canon
vocabulary. Each axis uses ~15-20 thematic markers so typical LLM-generated
agent output produces a non-zero signal.

For a future semantic-similarity replacement, swap the inner counters with
embedding distance to a canonical reference vector.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

# Lazy import to avoid circular deps
_persona_router = None


def _get_persona_router():
    global _persona_router
    if _persona_router is None:
        try:
            from veil_loader import load_module

            HERE = Path(__file__).resolve().parent.parent / "04_runtime"
            mod = load_module("persona_router", HERE / "persona_router.py")
            _persona_router = mod.get_router()
        except Exception:
            _persona_router = False
    return _persona_router if _persona_router is not False else None

# Thematic keyword banks — tuned against generated agent prose
_PRISM_WORDS = (
    "warm",
    "warmth",
    "guide",
    "guidance",
    "beauty",
    "beautiful",
    "light",
    "prism",
    "dawn",
    "lantern",
    "gentle",
    "soft",
    "candle",
    "glow",
    "radiant",
    "promise",
    "kindness",
    "welcome",
)
_QUASAR_WORDS = (
    "gravity",
    "hidden",
    "truth",
    "danger",
    "dangerous",
    "quasar",
    "dark",
    "darkness",
    "shadow",
    "shadows",
    "weight",
    "void",
    "ash",
    "fall",
    "buried",
    "secret",
    "secrets",
    "veil",
    "deep",
    "depths",
    "below",
    "ruin",
)
_DEPTH_WORDS = (
    "memory",
    "memories",
    "emotion",
    "emotional",
    "symbol",
    "symbolic",
    "resonance",
    "dream",
    "dreams",
    "whisper",
    "whispers",
    "echo",
    "echoes",
    "remember",
    "remembered",
    "feel",
    "felt",
    "ache",
    "longing",
    "tangled",
    "mirror",
    "thread",
    "story",
    "stories",
    "lost",
)


def _normalized_hits(text_lower: str, words: tuple[str, ...]) -> float:
    """Return a 0.0-1.0 score scaled to saturate at ~5 matches.

    Each unique match contributes 1/5 (so 5+ matches → 1.0). This rewards
    prose that uses thematic vocabulary without requiring the whole bank.
    """
    hits = sum(1 for w in words if w in text_lower)
    return min(1.0, hits / 5.0)


@dataclass
class AlignmentScore:
    prism_resonance: float
    dark_quasar_resonance: float
    emotional_depth: float
    canon_fidelity: float
    drift_risk: float
    role_fidelity: float

    @property
    def pass_gate(self) -> bool:
        return (
            self.canon_fidelity >= 0.75
            and self.drift_risk <= 0.35
            and self.role_fidelity >= 0.70
        )

    def to_dict(self):
        data = asdict(self)
        data["pass_gate"] = self.pass_gate
        return data


def score_text(text: str, role_keywords=None, canon_refs=None, agent_id: str | None = None) -> AlignmentScore:
    role_keywords = role_keywords or []
    canon_refs = canon_refs or []
    lowered = text.lower()

    # If agent_id is provided, pull persona-derived keyword bank
    if agent_id and not role_keywords:
        router = _get_persona_router()
        if router is not None:
            try:
                role_keywords = router.role_keywords(agent_id)
            except Exception:
                pass

    prism = _normalized_hits(lowered, _PRISM_WORDS)
    quasar = _normalized_hits(lowered, _QUASAR_WORDS)
    depth = _normalized_hits(lowered, _DEPTH_WORDS)

    if not role_keywords:
        role = 1.0
    else:
        matches = sum(1 for w in role_keywords if w.lower() in lowered)
        if len(role_keywords) <= 5:
            # Backward-compat for small explicit keyword lists (tests, direct calls)
            role = 1.0 if matches >= 1 else 0.0
        else:
            # Persona-derived bank (~20-25 words): 3+ hits = strong in-character
            role = min(1.0, matches / 3.0)

    canon = 0.9 if canon_refs else 0.6
    drift = 0.2 if canon_refs else 0.45

    return AlignmentScore(prism, quasar, depth, canon, drift, role)
