"""District unlock engine — resonance and Veil-state based unlocking.

Districts unlock through successful interactions, memory continuity,
and resonance thresholds. Veil state affects unlock difficulty:
- calm/still: easier to unlock hidden paths
- storm: harder, requires higher resonance
- quasar_active: most difficult, but can reveal paths invisible in other states
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DISTRICTS_PATH = Path("01_districts")


@dataclass
class UnlockCondition:
    min_resonance: float = 0.5
    min_interactions: int = 3
    required_emotional_tags: list[str] = field(default_factory=list)
    veil_states_allowed: list[str] = field(default_factory=lambda: ["calm", "still", "storm", "quasar_active"])
    veil_states_blocked: list[str] = field(default_factory=list)
    prerequisites: dict = field(default_factory=dict)  # districts_visited, has_lantern, lantern_used, etc.


@dataclass
class UnlockResult:
    unlocked: bool
    reason: str
    resonance: float = 0.0
    interactions: int = 0
    veil_state: str = ""
    missing_tags: list[str] = field(default_factory=list)


def check_unlock(
    district_id: str,
    resonance: float,
    interactions: int,
    emotional_tags: list[str],
    veil_state: str = "calm",
    player_state: dict | None = None,
) -> UnlockResult:
    """Check if a district unlocks given the current state.

    Args:
        district_id: District name (e.g., 'caetherra')
        resonance: Player's current resonance score (0.0-1.0)
        interactions: Number of meaningful interactions
        emotional_tags: Tags accumulated from interactions
        veil_state: Current Veil state (calm/still/storm/quasar_active)

    Returns:
        UnlockResult with unlock status and reason
    """
    # Load district config
    config_path = DISTRICTS_PATH / district_id / "unlock.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        condition = UnlockCondition(**config.get("unlock_conditions", {}))
        # Merge prerequisites from top-level config
        if "prerequisites" in config:
            condition.prerequisites = config["prerequisites"]
    else:
        # Default unlock conditions
        condition = UnlockCondition()

    # Check blocked Veil states
    if veil_state in condition.veil_states_blocked:
        return UnlockResult(
            unlocked=False,
            reason=f"Veil state '{veil_state}' blocks this path. The membrane is too distorted.",
            resonance=resonance,
            interactions=interactions,
            veil_state=veil_state,
        )

    # Check allowed Veil states
    if condition.veil_states_allowed and veil_state not in condition.veil_states_allowed:
        return UnlockResult(
            unlocked=False,
            reason=f"Cannot unlock during '{veil_state}'. Wait for a different Veil state.",
            resonance=resonance,
            interactions=interactions,
            veil_state=veil_state,
        )

    # Veil state difficulty modifiers
    resonance_adjusted = resonance
    if veil_state == "storm":
        resonance_adjusted -= 0.10  # Harder during storm
    elif veil_state == "quasar_active":
        resonance_adjusted -= 0.15  # Much harder during quasar

    # Check resonance threshold
    if resonance_adjusted < condition.min_resonance:
        return UnlockResult(
            unlocked=False,
            reason=f"Resonance too low ({resonance_adjusted:.2f} < {condition.min_resonance:.2f}). "
                   f"Deeper interaction needed.{' The Veil state makes this harder.' if veil_state in ('storm', 'quasar_active') else ''}",
            resonance=resonance_adjusted,
            interactions=interactions,
            veil_state=veil_state,
        )

    # Check interaction count
    if interactions < condition.min_interactions:
        return UnlockResult(
            unlocked=False,
            reason=f"Not enough meaningful interactions ({interactions} < {condition.min_interactions}). "
                   "Return and engage more deeply.",
            resonance=resonance_adjusted,
            interactions=interactions,
            veil_state=veil_state,
        )

    # Check required emotional tags
    missing = [tag for tag in condition.required_emotional_tags if tag not in emotional_tags]
    if missing:
        return UnlockResult(
            unlocked=False,
            reason=f"Missing emotional depth: {', '.join(missing)}. You haven't yet felt enough.",
            resonance=resonance_adjusted,
            interactions=interactions,
            veil_state=veil_state,
            missing_tags=missing,
        )

    # Check prerequisites (districts visited, flags, etc.)
    if player_state and condition.prerequisites:
        visited = set(player_state.get("unlocked_districts") or [])
        required_visits = condition.prerequisites.get("districts_visited", [])
        for req_district in required_visits:
            if req_district not in visited:
                return UnlockResult(
                    unlocked=False,
                    reason=f"You must visit {req_district} before this path can open.",
                    resonance=resonance_adjusted,
                    interactions=interactions,
                    veil_state=veil_state,
                )
        if condition.prerequisites.get("has_lantern") and not player_state.get("has_lantern"):
            return UnlockResult(
                unlocked=False,
                reason="You carry no lantern. The threshold gate requires it.",
                resonance=resonance_adjusted,
                interactions=interactions,
                veil_state=veil_state,
            )
        if condition.prerequisites.get("lantern_used") and not player_state.get("lantern_used"):
            return UnlockResult(
                unlocked=False,
                reason="Your lantern has not yet revealed anything. Use it first.",
                resonance=resonance_adjusted,
                interactions=interactions,
                veil_state=veil_state,
            )

    # All conditions met
    return UnlockResult(
        unlocked=True,
        reason=f"The path opens. Your resonance ({resonance_adjusted:.2f}) and depth ({interactions} interactions) have earned it.",
        resonance=resonance_adjusted,
        interactions=interactions,
        veil_state=veil_state,
    )


# Special: quasar_active can reveal paths invisible in other states
def check_quasar_reveal(
    district_id: str,
    resonance: float,
    veil_state: str = "quasar_active",
) -> UnlockResult:
    """Check if a hidden quasar-revealed path opens during quasar_active state.

    These are paths that ONLY appear during quasar_active —
    the gravity of truth pulls them into visibility.
    """
    if veil_state != "quasar_active":
        return UnlockResult(
            unlocked=False,
            reason="This path only reveals itself under the Quasar's gravity.",
            resonance=resonance,
            veil_state=veil_state,
        )

    if resonance < 0.6:
        return UnlockResult(
            unlocked=False,
            reason=f"The Quasar pulls, but your resonance ({resonance:.2f}) is not yet deep enough to see.",
            resonance=resonance,
            veil_state=veil_state,
        )

    return UnlockResult(
        unlocked=True,
        reason="Under the Quasar's gravity, a hidden pathmaterializes. Truth pulls the worthy closer.",
        resonance=resonance,
        veil_state=veil_state,
    )
