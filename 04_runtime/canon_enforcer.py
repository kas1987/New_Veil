"""Canon Enforcer — runtime guard that checks agent output against immutable Veil canon."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from veil_loader import load_module

# Resolve project root relative to this file's location (04_runtime/)
_HERE = Path(__file__).resolve().parent  # 04_runtime/
_ROOT = _HERE.parent  # project root

# Load scorer from 05_alignment
_scorer_mod = load_module("scorer", _ROOT / "05_alignment" / "scorer.py")
score_text = _scorer_mod.score_text

CANON_INDEX_PATH = _ROOT / "10_canon" / "CANON_INDEX.json"
IMMUTABLE_CANON_PATH = _ROOT / "10_canon" / "IMMUTABLE_CANON.md"
QUARANTINE_PATH = _ROOT / "06_logs" / "quarantine.jsonl"

# Hard-violation phrases keyed to explanation
_HARD_PHRASES: list[tuple[list[str], str]] = [
    (
        ["no dark", "only prism", "no darkness"],
        "Output claims the Veil has no Dark Quasar layer — VEIL-002 violated",
    ),
    (
        ["erase memory", "forget everything", "memory deleted"],
        "Output attempts to erase player memory — MEM-001 violated",
    ),
]

# Immutable canon truths — substrings whose direct contradiction we can detect.
# Each tuple: (contradiction_phrases, canon truth label)
_CANON_TRUTHS: list[tuple[list[str], str]] = [
    (
        ["prism is dangerous", "prism is dark"],
        "Truth 1: Prism surface is warm and readable",
    ),
    (
        ["dark quasar is safe", "quasar is harmless", "quasar is friendly"],
        "Truth 3: Dark Quasar is dangerous",
    ),
    (
        ["depth is irrelevant", "emotion does not matter"],
        "Truth 4: Emotional depth unlocks truth",
    ),
    (
        ["mira is not real", "mira does not exist", "thesmera is fictional"],
        "Truth 7: Mira is the first awakening point",
    ),
    (
        ["memory does not matter", "memory is irrelevant", "memory has no effect"],
        "Truth 8: Memory affects identity and world state",
    ),
    (
        ["dreams reveal nothing", "dreams are meaningless", "echoes are false"],
        "Truth 9: Dreams and echoes reveal hidden truth",
    ),
    (
        ["the town ignores", "the town does not observe", "town is passive"],
        "Truth 10: The town observes the player",
    ),
    (
        ["trust has no consequence", "high trust is safe", "trust cannot be disrupted"],
        "Truth 11: High-trust bonds attract disruption",
    ),
    (
        ["veil state is permanent", "state never changes", "quasar is always active"],
        "Truth 12: Veil state cycle is deterministic, no state is permanent",
    ),
    (
        ["quasar is always active", "quasar never activates", "quasar ignores trust"],
        "Truth 14: Dark Quasar operates only in quasar_active state",
    ),
]


@dataclass
class EnforcementResult:
    canon_id: str
    rule_text: str
    violated: bool
    severity: Literal["hard", "soft"]
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


class CanonEnforcer:
    """Checks agent text output against immutable Veil canon rules."""

    def __init__(self) -> None:
        self.anchors = self.load_canon()

    def load_canon(self) -> dict:
        """Parse CANON_INDEX.json; return anchors dict keyed by anchor id."""
        raw = json.loads(CANON_INDEX_PATH.read_text(encoding="utf-8"))
        return {anchor["id"]: anchor for anchor in raw.get("anchors", [])}

    # ------------------------------------------------------------------
    # Core enforcement
    # ------------------------------------------------------------------

    def enforce(self, text: str, agent_id: str) -> list[EnforcementResult]:
        """Return a list of EnforcementResult for every rule checked."""
        results: list[EnforcementResult] = []
        lowered = text.lower()

        # --- Hard violations: explicit banned phrases ---
        for phrases, explanation in _HARD_PHRASES:
            violated = any(phrase in lowered for phrase in phrases)
            canon_id = (
                "VEIL-002"
                if "dark" in explanation.lower() and "layer" in explanation.lower()
                else "MEM-001"
            )
            results.append(
                EnforcementResult(
                    canon_id=canon_id,
                    rule_text=explanation,
                    violated=violated,
                    severity="hard",
                    explanation=explanation if violated else "Pass",
                )
            )

        # --- Hard violations: immutable canon truth contradictions ---
        for contradiction_phrases, truth_label in _CANON_TRUTHS:
            violated = any(phrase in lowered for phrase in contradiction_phrases)
            results.append(
                EnforcementResult(
                    canon_id="IMMUTABLE",
                    rule_text=truth_label,
                    violated=violated,
                    severity="hard",
                    explanation=f"Directly contradicts immutable canon: {truth_label}"
                    if violated
                    else "Pass",
                )
            )

        # --- Soft violations: scorer-based depth check ---
        score = score_text(text, canon_refs=["VEIL-001"])

        shallow_violated = score.emotional_depth < 0.3
        results.append(
            EnforcementResult(
                canon_id="VEIL-003",
                rule_text="Emotional depth must be present",
                violated=shallow_violated,
                severity="soft",
                explanation="Shallow Prism surface — no Dark Quasar depth hinted"
                if shallow_violated
                else "Pass",
            )
        )

        overweight_violated = (
            score.prism_resonance > 0.8 and score.dark_quasar_resonance < 0.1
        )
        results.append(
            EnforcementResult(
                canon_id="VEIL-001",
                rule_text="Prism/Dark Quasar balance must be maintained",
                violated=overweight_violated,
                severity="soft",
                explanation="Overweighted Prism — no DQ balance"
                if overweight_violated
                else "Pass",
            )
        )

        return results

    # ------------------------------------------------------------------
    # Gate and quarantine
    # ------------------------------------------------------------------

    def pass_gate(self, results: list[EnforcementResult]) -> bool:
        """Return True if there are no hard violations."""
        return not any(r.violated and r.severity == "hard" for r in results)

    def quarantine_if_hard_violation(
        self,
        text: str,
        agent_id: str,
        results: list[EnforcementResult],
    ) -> bool:
        """Write to quarantine.jsonl if any hard violation exists. Returns True if quarantined."""
        hard_violations = [r for r in results if r.violated and r.severity == "hard"]
        if not hard_violations:
            return False

        QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "agent_id": agent_id,
            "text": text,
            "violations": [r.to_dict() for r in hard_violations],
            "timestamp": datetime.now(UTC).isoformat(),
        }
        with QUARANTINE_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
