"""LLM-based player intent classifier.

Categorizes player input into a small intent taxonomy so the orchestrator can
modulate depth deltas and agent response style. Falls back to a lexical heuristic
(then to `"unclear"`) if Ollama is unreachable, so tests stay offline-safe.

Taxonomy:
  curious      — asking, exploring, wanting more
  challenging  — pushing back, testing, calling out
  shallow      — surface only, content with appearances
  deep         — engaging with depth, emotional risk, honesty
  emotional    — vulnerable, confessional, raw
  hostile      — rude, dismissive, attacking
  unclear      — couldn't classify
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Literal

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
INTENT_MODEL = os.environ.get("VEIL_INTENT_MODEL", "qwen3:8b")
INTENT_TIMEOUT = float(os.environ.get("VEIL_INTENT_TIMEOUT", "15"))

IntentLabel = Literal[
    "curious", "challenging", "shallow", "deep", "emotional", "hostile", "unclear"
]

VALID_LABELS = {
    "curious",
    "challenging",
    "shallow",
    "deep",
    "emotional",
    "hostile",
    "unclear",
}

# Map each intent to a depth_delta multiplier the orchestrator can apply.
# Bound from -1.5 (shallow drag) to +2.0 (deep boost).
DEPTH_MODIFIER: dict[str, float] = {
    "deep": 2.0,
    "emotional": 1.5,
    "curious": 1.0,
    "challenging": 0.5,
    "unclear": 0.0,
    "shallow": -1.0,
    "hostile": -1.5,
}

_SYSTEM_PROMPT = (
    "You classify a player's intent in a symbolic narrative game. "
    "Read the player's message and return EXACTLY ONE word from this list: "
    "curious, challenging, shallow, deep, emotional, hostile, unclear. "
    "Respond with the single word only, no punctuation, no explanation."
)


_HEURISTIC_RULES = (
    # (pattern, label) — first match wins. Order: strong-signal rules first so
    # specific labels (hostile/emotional/deep) win over broader ones (curious).
    (re.compile(r"\b(fuck|shit|stupid|idiot|hate|garbage|trash)\b", re.I), "hostile"),
    (
        re.compile(
            r"\b(love|hurt|cry|broken|lost|alone|afraid|grief|miss|need)\b", re.I
        ),
        "emotional",
    ),
    (
        re.compile(r"\b(truth|deeper|honest|memory|dream|veil|shadow|gravity)\b", re.I),
        "deep",
    ),
    (
        re.compile(r"\b(no|wrong|lie|prove|deflect|hiding|really|but)\b", re.I),
        "challenging",
    ),
    (
        re.compile(r"\b(fine|whatever|sure|ok|okay|nice|cool|yeah)\b", re.I),
        "shallow",
    ),
    (
        re.compile(
            r"\b(why|what|how|tell me|explain|show me|who|where|reveal)\b", re.I
        ),
        "curious",
    ),
)


def _heuristic_classify(text: str) -> IntentLabel:
    """Fallback lexical classifier — used if LLM is unreachable."""
    t = text.strip()
    if not t:
        return "unclear"
    for pat, label in _HEURISTIC_RULES:
        if pat.search(t):
            return label  # type: ignore[return-value]
    return "unclear"


def _ollama_classify(text: str, model: str, timeout: float) -> IntentLabel | None:
    body = json.dumps(
        {
            "model": model,
            "prompt": text,
            "system": _SYSTEM_PROMPT,
            "stream": False,
            "options": {"num_predict": 8, "temperature": 0.0},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    raw = (data.get("response") or "").strip().lower()
    # Strip punctuation/quotes
    raw = re.sub(r"[^a-z]", "", raw)
    if raw in VALID_LABELS:
        return raw  # type: ignore[return-value]
    # Sometimes the model emits a sentence; first word
    first = raw[:30]
    for label in VALID_LABELS:
        if first.startswith(label):
            return label  # type: ignore[return-value]
    return None


# Process-wide LRU-ish cache for classifications (input → label) to avoid
# re-classifying identical input. Bounded to avoid unbounded growth.
_CACHE: dict[str, dict] = {}
_CACHE_LIMIT = 256


def classify_intent(
    text: str,
    use_llm: bool | None = None,
) -> dict:
    """Classify player intent. Returns {label, depth_modifier, source}.

    source ∈ {"llm", "heuristic", "cache"}.
    """
    if not text or not text.strip():
        return {"label": "unclear", "depth_modifier": 0.0, "source": "heuristic"}

    key = text.strip().lower()
    if key in _CACHE:
        return {**_CACHE[key], "source": "cache"}

    if use_llm is None:
        use_llm = os.environ.get("VEIL_USE_LLM_INTENT", "1") in ("1", "true", "True")

    label: IntentLabel | None = None
    source = "heuristic"
    if use_llm:
        label = _ollama_classify(text, INTENT_MODEL, INTENT_TIMEOUT)
        if label:
            source = "llm"

    if label is None:
        label = _heuristic_classify(text)
        source = "heuristic"

    result = {
        "label": label,
        "depth_modifier": DEPTH_MODIFIER.get(label, 0.0),
    }

    if len(_CACHE) >= _CACHE_LIMIT:
        # Drop oldest (insertion-order dict) — simple FIFO eviction
        try:
            _CACHE.pop(next(iter(_CACHE)))
        except StopIteration:
            pass
    _CACHE[key] = result

    return {**result, "source": source}


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or "Why did you hesitate when I asked about her?"
    print(json.dumps(classify_intent(text), indent=2))
