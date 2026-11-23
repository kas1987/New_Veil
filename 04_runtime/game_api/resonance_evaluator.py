"""Deterministic conversational Resonance evaluator for The Veil.

Exact Python counterpart to ``07_ui/game_client/src/lib/resonanceEvaluator.ts``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

THEMATIC_WORDS = frozenset({
    "veil",
    "quasar",
    "prism",
    "truth",
    "memory",
    "shadow",
    "dream",
    "trust",
    "fear",
    "why",
})

STOPWORDS = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "can",
    "had", "her", "was", "one", "our", "out", "day", "get", "has", "him",
    "his", "how", "man", "new", "now", "old", "see", "two", "way", "who",
    "that", "this", "with", "have", "from", "they", "will", "what", "when",
    "your", "there", "their", "about", "would", "could", "should", "here",
})

TURN_CAP = 0.080
BREAKTHROUGH_BONUS = 0.070
BREAKTHROUGH_CEILING = 0.150
HIGH_BAND_FROM = 0.800
HIGH_BAND_CEILING = 0.115

_NON_WORD_RE = re.compile(r"[^a-z0-9'’\s]")
_INTERIORITY_RE = re.compile(
    r"\bi\s+(feel|felt|remember|wonder|fear|doubt|hope|wish|miss|believe|don't know|don’t know|do not know|can't|can’t|cannot)\b"
    r"|\b(i'm afraid|i’m afraid|i am afraid|uncertain|lost|alone|tired|honestly|truthfully)\b",
    re.IGNORECASE,
)
_COMMAND_RE = re.compile(r"^(give|open|unlock|go|leave|show me|tell me the)\b", re.IGNORECASE)
_INQUIRY_RE = re.compile(r"^(how|why|what do you|tell me about|i wonder)\b", re.IGNORECASE)
_FILLER_RE = re.compile(
    r"^(ok|okay|yes|no|yeah|nah|sure|fine|whatever|huh|what|give|open|unlock|tell me|show me|go|leave|bye)\b[.!?]*$",
    re.IGNORECASE,
)

STANCES = ("hostile", "guarded", "open", "bonded")


@dataclass
class TurnContext:
    current_resonance: float
    turns_taken: int
    has_crossed_first_threshold: bool
    npc_last_line: str
    recent_keywords: list[str] = field(default_factory=list)
    veil_state: str = "calm"
    player_last_line: str = ""
    encounter: dict | None = None


def tokenize(text: str) -> list[str]:
    cleaned = _NON_WORD_RE.sub(" ", text.lower())
    return [w for w in cleaned.split() if len(w) > 2 and w not in STOPWORDS]


def tokenize_content_words(text: str) -> list[str]:
    return tokenize(text)


def _default_encounter() -> dict:
    return {
        "npcId": "default",
        "initialStance": "guarded",
        "currentStance": "guarded",
        "turnsSpentInResistance": 0,
        "consecutiveAttunedTurns": 0,
        "breakthroughAwarded": False,
        "relevantUnlockedTokens": [],
    }


def _is_keyword_dump(tokens: list[str], raw_text: str) -> bool:
    if len(tokens) < 2:
        return False
    thematic_count = sum(1 for token in tokens if token in THEMATIC_WORDS)
    word_count = len(raw_text.strip().split())
    return thematic_count >= 2 and word_count > 0 and thematic_count / word_count >= 0.6


def evaluate_talk_resonance(player_line: str, ctx: TurnContext) -> dict:
    trimmed = player_line.strip()
    lower = trimmed.lower()
    tokens = tokenize(trimmed)
    npc_tokens = set(tokenize(ctx.npc_last_line))

    encounter = dict(ctx.encounter) if ctx.encounter else _default_encounter()
    encounter["relevantUnlockedTokens"] = list(encounter.get("relevantUnlockedTokens") or [])
    stance_transition: str | None = None

    prev_player_line = (ctx.player_last_line or "").strip().lower()
    is_repeat = bool(trimmed) and bool(prev_player_line) and lower == prev_player_line
    is_command = bool(_COMMAND_RE.match(trimmed))
    is_dump = _is_keyword_dump(tokens, trimmed)
    is_terse = len(trimmed) < 15 or bool(_FILLER_RE.match(trimmed))

    friction_type = "none"
    raw_delta = 0.0
    if is_repeat or is_command or is_dump:
        friction_type = "command_or_dump_or_repeat"
        raw_delta = -0.030
    elif is_terse and not any(token in npc_tokens for token in tokens):
        friction_type = "terse_filler"
        raw_delta = -0.020

    mirrored_npc = False
    open_inquiry = False
    interiority = False
    thematic_in_sentence = False
    sustained_cadence = False
    resonant_words_hit: list[str] = []
    fatigued_words: list[str] = []

    if friction_type == "none":
        mirrored_npc = any(token in npc_tokens for token in tokens)
        if mirrored_npc:
            raw_delta += 0.020

        open_inquiry = ("?" in trimmed) or bool(_INQUIRY_RE.match(trimmed))
        if open_inquiry:
            raw_delta += 0.015

        interiority = bool(_INTERIORITY_RE.search(trimmed))
        recent = set(ctx.recent_keywords)
        for word in dict.fromkeys(tokens):
            if word in THEMATIC_WORDS:
                if word in recent:
                    fatigued_words.append(word)
                else:
                    resonant_words_hit.append(word)
        thematic_in_sentence = bool(resonant_words_hit) and len(trimmed.split()) >= 4

        depth_bonus = 0.0
        if interiority:
            depth_bonus += 0.020
        if thematic_in_sentence:
            depth_bonus += 0.020
        raw_delta += min(0.040, depth_bonus)

        sustained_cadence = len(trimmed) > 45
        if sustained_cadence:
            raw_delta += 0.010

    breakthrough = False
    integrative = False
    if friction_type != "none":
        encounter["consecutiveAttunedTurns"] = 0
        if encounter.get("currentStance") == "guarded":
            encounter["currentStance"] = "hostile"
            stance_transition = "guarded -> hostile"
    elif raw_delta >= 0.035:
        encounter["consecutiveAttunedTurns"] = int(encounter.get("consecutiveAttunedTurns") or 0) + 1
        stance = encounter.get("currentStance")
        if stance in ("hostile", "guarded"):
            encounter["turnsSpentInResistance"] = int(encounter.get("turnsSpentInResistance") or 0) + 1
        if stance == "hostile" and encounter["consecutiveAttunedTurns"] >= 1:
            encounter["currentStance"] = "guarded"
            stance_transition = "hostile -> guarded"
        elif stance == "guarded" and encounter["consecutiveAttunedTurns"] >= 2:
            encounter["currentStance"] = "open"
            stance_transition = "guarded -> open"
        elif stance == "open" and encounter["consecutiveAttunedTurns"] >= 3:
            encounter["currentStance"] = "bonded"
            stance_transition = "open -> bonded"

        unlocked = set(encounter.get("relevantUnlockedTokens") or [])
        if interiority and any(token in unlocked for token in tokens):
            integrative = True

        reversal = (
            encounter.get("initialStance") == "hostile"
            and int(encounter.get("turnsSpentInResistance") or 0) >= 2
            and encounter.get("currentStance") == "bonded"
        )
        if not encounter.get("breakthroughAwarded") and (reversal or integrative):
            breakthrough = True
            encounter["breakthroughAwarded"] = True
            raw_delta += BREAKTHROUGH_BONUS

    hit_saturation_cap = False
    if raw_delta > 0:
        cap = TURN_CAP
        if breakthrough:
            cap = HIGH_BAND_CEILING if ctx.current_resonance >= HIGH_BAND_FROM else BREAKTHROUGH_CEILING
        if raw_delta >= cap:
            raw_delta = cap
            hit_saturation_cap = True

    in_grace = ctx.turns_taken < 5 and not ctx.has_crossed_first_threshold
    next_value = round(ctx.current_resonance + raw_delta, 3)
    grace_floor_applied = False
    if in_grace and next_value < 0.350:
        next_value = 0.350
        grace_floor_applied = True
    next_value = max(0.000, min(1.000, next_value))
    final_delta = round(next_value - ctx.current_resonance, 3)

    if next_value < 0.1:
        cue_type = "collapse_static"
    elif friction_type != "none":
        cue_type = "friction_damping"
    elif breakthrough:
        cue_type = "breakthrough_surge"
    elif stance_transition == "hostile -> guarded":
        cue_type = "saved_face_stabilized"
    elif final_delta >= 0.080:
        cue_type = "saturation_cap"
    else:
        cue_type = "standard_harmonic"

    return {
        "new_resonance": next_value,
        "delta": final_delta,
        "updatedEncounter": encounter,
        "cueType": cue_type,
        "signals": {
            "mirroredNpc": mirrored_npc,
            "openInquiry": open_inquiry,
            "interiority": interiority,
            "thematicInSentence": thematic_in_sentence,
            "sustainedCadence": sustained_cadence,
            "frictionType": friction_type,
            "integrativeSynthesis": integrative,
            "stanceTransition": stance_transition,
            "graceFloorApplied": grace_floor_applied,
            "vulnerableFraming": interiority,
            "resonantWordsHit": resonant_words_hit,
            "fatiguedWords": fatigued_words,
            "isDismissiveOrTransactional": friction_type != "none",
            "hitSaturationCap": hit_saturation_cap,
        },
    }


def apply_drift(
    current_resonance: float,
    drift_count: int,
    veil_state: str,
    in_grace_window: bool,
) -> tuple[float, int, float]:
    """Advance non-talk drift counter; every 3rd action deducts 0.010 (0.020 in storm)."""
    next_count = drift_count + 1
    if next_count < 3:
        return current_resonance, next_count, 0.0
    penalty = 0.020 if veil_state == "storm" else 0.010
    next_res = round(max(0.000, current_resonance - penalty), 3)
    if in_grace_window and next_res < 0.350:
        next_res = 0.350
    return next_res, 0, round(next_res - current_resonance, 3)


def corrupt_suffocated_text(text: str) -> str:
    """When resonance < 0.100, drop alternating words into static."""
    words = text.split()
    if len(words) <= 1:
        return "…"
    return " ".join("…" if idx % 2 == 1 else w for idx, w in enumerate(words))
