"""Deterministic conversational Resonance evaluator for The Veil.

Exact Python counterpart to ``07_ui/game_client/src/lib/resonanceEvaluator.ts``.
Three-timescale model:
1. Immediate encounter stance (hostile <-> guarded <-> open <-> bonded) in 5-6 turns.
2. Personal NPC Bond (0.0-100.0) with optional per-NPC personality_weights (~25 turns).
3. Global Town Resonance (0.0-1000.0) with a +50.0 per-NPC soft taper (0.15x).
"""

from __future__ import annotations

import math
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

TOWN_MAX = 1000.0
GRACE_FLOOR = 350.0
COLLAPSE_THRESHOLD = 100.0
QUASAR_RESONANCE_THRESHOLD = 600.0

TURN_CAP = 2.5
ATTUNED_MIN_DELTA = 1.1
BREAKTHROUGH_BONUS = 3.5
BREAKTHROUGH_CEILING = 6.0
HIGH_BAND_FROM = 800.0
HIGH_BAND_CEILING = 4.0
HOSTILE_DISMISSAL_PENALTY = -1.8
TRUST_RUPTURE_PENALTY = -3.0
QUASAR_NEGATIVE_MULTIPLIER = 1.25

NPC_CONTRIBUTION_SOFT_CAP = 50.0
NPC_TAPER_MULTIPLIER = 0.15
NPC_BOND_GAIN_MULTIPLIER = 1.6
NPC_BOND_LOSS_MULTIPLIER = 1.5
NPC_BREAKTHROUGH_BOND_BONUS = 10.0

_NON_WORD_RE = re.compile(r"[^a-z0-9'’\s]")
_INTERIORITY_RE = re.compile(
    r"\bi\s+(feel|felt|remember|wonder|fear|doubt|hope|wish|miss|believe|don't know|don’t know|do not know|can't|can’t|cannot)\b"
    r"|\b(i'm afraid|i’m afraid|i am afraid|uncertain|lost|alone|tired|honestly|truthfully)\b",
    re.IGNORECASE,
)
_HOSTILE_DISMISSAL_RE = re.compile(
    r"\b(shut up|stop talking|don't care|don’t care|do not care|waste of time|pathetic|useless|boring|stupid|annoying|liar|you're lying|you’re lying|you are lying|leave me alone|get lost|whatever you say|fake town)\b",
    re.IGNORECASE,
)
_COMMAND_RE = re.compile(r"^(give|open|unlock|go|leave|show me|tell me the)\b", re.IGNORECASE)
_INQUIRY_RE = re.compile(r"^(how|why|what do you|tell me about|i wonder)\b", re.IGNORECASE)
_FILLER_RE = re.compile(
    r"^(ok|okay|yes|no|yeah|nah|sure|fine|whatever|huh|what|give|open|unlock|tell me|show me|go|leave|bye)\b[.!?]*$",
    re.IGNORECASE,
)

STANCES = ("hostile", "guarded", "open", "bonded")


def _round2(value: float) -> float:
    """Round half-away-from-zero to 2 decimal places identically in Python and JS."""
    if abs(value) < 1e-12:
        return 0.0
    sign = -1.0 if value < 0 else 1.0
    return (sign * math.floor(abs(value) * 100.0 + 0.5 + 1e-9)) / 100.0


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
    personality_weights: dict[str, float] | None = None


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
        "consecutiveFrictionTurns": 0,
        "breakthroughAwarded": False,
        "relevantUnlockedTokens": [],
        "npcBond": 0.0,
        "townContribution": 0.0,
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
    encounter.setdefault("npcBond", 0.0)
    encounter.setdefault("townContribution", 0.0)
    stance_transition: str | None = None

    weights = ctx.personality_weights or {}
    w_mirror = float(weights.get("mirror", 1.0))
    w_inquiry = float(weights.get("inquiry", 1.0))
    w_interiority = float(weights.get("interiority", 1.0))
    w_thematic = float(weights.get("thematic", 1.0))
    w_cadence = float(weights.get("cadence", 1.0))

    prev_player_line = (ctx.player_last_line or "").strip().lower()
    is_hostile_dismissal = bool(_HOSTILE_DISMISSAL_RE.search(trimmed))
    is_repeat = bool(trimmed) and bool(prev_player_line) and lower == prev_player_line
    is_command = bool(_COMMAND_RE.match(trimmed))
    is_dump = _is_keyword_dump(tokens, trimmed)
    is_terse = len(trimmed) < 15 or bool(_FILLER_RE.match(trimmed))

    friction_type = "none"
    raw_delta = 0.0
    if is_hostile_dismissal:
        friction_type = "hostile_dismissal"
        raw_delta = HOSTILE_DISMISSAL_PENALTY
    elif is_repeat or is_command or is_dump:
        friction_type = "command_or_dump_or_repeat"
        raw_delta = -1.2
    elif is_terse and not any(token in npc_tokens for token in tokens):
        friction_type = "terse_filler"
        raw_delta = -0.8

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
            raw_delta += _round2(0.6 * w_mirror)

        open_inquiry = ("?" in trimmed) or bool(_INQUIRY_RE.match(trimmed))
        if open_inquiry:
            raw_delta += _round2(0.5 * w_inquiry)

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
            depth_bonus += 0.6 * w_interiority
        if thematic_in_sentence:
            depth_bonus += 0.6 * w_thematic
        raw_delta += _round2(min(1.2, depth_bonus))

        sustained_cadence = len(trimmed) > 45
        if sustained_cadence:
            raw_delta += _round2(0.3 * w_cadence)
        raw_delta = _round2(raw_delta)

    breakthrough = False
    integrative = False
    trust_rupture = False
    quasar_amplified = False
    prev_stance = encounter.get("currentStance", "guarded")

    if friction_type != "none":
        encounter["consecutiveAttunedTurns"] = 0
        consec_friction = int(encounter.get("consecutiveFrictionTurns") or 0) + 1
        encounter["consecutiveFrictionTurns"] = consec_friction

        if friction_type == "hostile_dismissal":
            if prev_stance == "bonded":
                encounter["currentStance"] = "guarded"
                stance_transition = "bonded -> guarded"
                trust_rupture = True
                raw_delta = TRUST_RUPTURE_PENALTY
            elif prev_stance == "open":
                encounter["currentStance"] = "hostile"
                stance_transition = "open -> hostile"
                trust_rupture = True
                raw_delta = TRUST_RUPTURE_PENALTY
            elif prev_stance == "guarded":
                encounter["currentStance"] = "hostile"
                stance_transition = "guarded -> hostile"
        else:
            if prev_stance == "guarded":
                encounter["currentStance"] = "hostile"
                stance_transition = "guarded -> hostile"
            elif prev_stance == "open" and consec_friction >= 2:
                encounter["currentStance"] = "guarded"
                stance_transition = "open -> guarded"
            elif prev_stance == "bonded" and consec_friction >= 2:
                encounter["currentStance"] = "open"
                stance_transition = "bonded -> open"

        # Canon #15: Dark Quasar amplifies negative signals by 25% on high-trust/high-resonance bonds
        if ctx.veil_state == "quasar_active" and (
            ctx.current_resonance >= QUASAR_RESONANCE_THRESHOLD or prev_stance in ("open", "bonded")
        ):
            raw_delta = _round2(raw_delta * QUASAR_NEGATIVE_MULTIPLIER)
            quasar_amplified = True
    elif raw_delta >= ATTUNED_MIN_DELTA:
        encounter["consecutiveFrictionTurns"] = 0
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
            raw_delta = _round2(raw_delta + BREAKTHROUGH_BONUS)

    hit_saturation_cap = False
    if raw_delta > 0:
        cap = TURN_CAP
        if breakthrough:
            cap = HIGH_BAND_CEILING if ctx.current_resonance >= HIGH_BAND_FROM else BREAKTHROUGH_CEILING
        if raw_delta >= cap:
            raw_delta = cap
            hit_saturation_cap = True

    # Personal NPC Bond updates from pre-taper raw_delta (~25 attuned turns to reach 100.0)
    prev_bond = float(encounter.get("npcBond") or 0.0)
    if breakthrough:
        bond_delta = NPC_BREAKTHROUGH_BOND_BONUS
    elif raw_delta > 0:
        bond_delta = _round2(raw_delta * NPC_BOND_GAIN_MULTIPLIER)
    elif raw_delta < 0:
        bond_delta = _round2(raw_delta * NPC_BOND_LOSS_MULTIPLIER)
    else:
        bond_delta = 0.0
    next_bond = max(0.0, min(100.0, _round2(prev_bond + bond_delta)))
    encounter["npcBond"] = next_bond

    # Soft taper per NPC after +50.0 global Town Resonance contribution (positive gains only)
    prev_contrib = float(encounter.get("townContribution") or 0.0)
    npc_taper_applied = False
    town_delta = raw_delta
    if raw_delta > 0:
        if prev_contrib >= NPC_CONTRIBUTION_SOFT_CAP:
            town_delta = _round2(raw_delta * NPC_TAPER_MULTIPLIER)
            npc_taper_applied = True
        elif prev_contrib + raw_delta > NPC_CONTRIBUTION_SOFT_CAP:
            full_part = NPC_CONTRIBUTION_SOFT_CAP - prev_contrib
            rem_part = raw_delta - full_part
            town_delta = _round2(full_part + rem_part * NPC_TAPER_MULTIPLIER)
            npc_taper_applied = True
        encounter["townContribution"] = _round2(prev_contrib + town_delta)

    in_grace = ctx.turns_taken < 5 and not ctx.has_crossed_first_threshold
    next_value = _round2(ctx.current_resonance + town_delta)
    grace_floor_applied = False
    if in_grace and next_value < GRACE_FLOOR:
        next_value = GRACE_FLOOR
        grace_floor_applied = True
    next_value = max(0.0, min(TOWN_MAX, next_value))
    final_delta = _round2(next_value - ctx.current_resonance)

    if next_value < COLLAPSE_THRESHOLD:
        cue_type = "collapse_static"
    elif trust_rupture:
        cue_type = "trust_rupture"
    elif friction_type != "none":
        cue_type = "friction_damping"
    elif breakthrough:
        cue_type = "breakthrough_surge"
    elif stance_transition == "hostile -> guarded":
        cue_type = "saved_face_stabilized"
    elif hit_saturation_cap and not npc_taper_applied:
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
            "trustRupture": trust_rupture,
            "quasarAmplified": quasar_amplified,
            "npcTaperApplied": npc_taper_applied,
            "npcBond": next_bond,
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
    """Advance non-talk drift counter; every 3rd action deducts 0.5 (1.0 in storm)."""
    next_count = drift_count + 1
    if next_count < 3:
        return current_resonance, next_count, 0.0
    penalty = 1.0 if veil_state == "storm" else 0.5
    next_res = _round2(max(0.0, current_resonance - penalty))
    if in_grace_window and next_res < GRACE_FLOOR:
        next_res = GRACE_FLOOR
    return next_res, 0, _round2(next_res - current_resonance)


def corrupt_suffocated_text(text: str) -> str:
    """When resonance < 100.0, drop alternating words into static."""
    words = text.split()
    if len(words) <= 1:
        return "…"
    return " ".join("…" if idx % 2 == 1 else w for idx, w in enumerate(words))
