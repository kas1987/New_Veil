"""Self-contained Sister Prism system primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SisterFacet(Enum):
    """Enumeration of the nine canonical Sister facets."""

    COMPASSION = "compassion"
    PRIDE = "pride"
    DECEIT = "deceit"
    WRATH = "wrath"
    ISOLATION = "isolation"
    MANIPULATION = "manipulation"
    ENVY = "envy"
    DEATH = "death"
    LUST = "lust"


@dataclass
class PrismExperience:
    """Single Sister perspective on a gameplay event."""

    sister_id: str
    facet: SisterFacet
    event_id: str
    interpretation: str
    emotional_tone: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    veil_proximity: float = 0.0


@dataclass
class ConvergenceMoment:
    """Multiple Sisters interpreting the same event."""

    event_id: str
    facets: List[SisterFacet]
    interpretations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    convergence_score: float = 0.0


class SisterPrismSystem:
    """Tracks collected facets and convergence moments."""

    def __init__(self) -> None:
        self.collected_facets: List[SisterFacet] = []
        self.prism_experiences: List[PrismExperience] = []
        self.convergence_moments: List[ConvergenceMoment] = []

    # --------------------------------------------------------------------- #
    # Core operations
    # --------------------------------------------------------------------- #
    def add_prism_experience(
        self,
        *,
        sister_id: str,
        facet: SisterFacet,
        event_id: str,
        interpretation: str,
        emotional_tone: str = "neutral",
        veil_proximity: float = 0.0,
    ) -> PrismExperience:
        """Record a new prism experience and update aggregate state."""

        experience = PrismExperience(
            sister_id=sister_id,
            facet=facet,
            event_id=event_id,
            interpretation=interpretation,
            emotional_tone=emotional_tone,
            veil_proximity=veil_proximity,
        )
        self.prism_experiences.append(experience)

        if facet not in self.collected_facets:
            self.collected_facets.append(facet)

        self._check_convergence(event_id)
        return experience

    def _check_convergence(self, event_id: str) -> Optional[ConvergenceMoment]:
        """Detect whether multiple Sisters have interpreted the same event."""

        event_experiences = [
            exp for exp in self.prism_experiences if exp.event_id == event_id
        ]
        if len(event_experiences) < 2:
            return None

        unique_interpretations = len(
            {exp.interpretation for exp in event_experiences}
        )
        convergence_score = 1.0 - (unique_interpretations / len(event_experiences))

        convergence = ConvergenceMoment(
            event_id=event_id,
            facets=[exp.facet for exp in event_experiences],
            interpretations=[exp.interpretation for exp in event_experiences],
            convergence_score=convergence_score,
        )

        if not any(moment.event_id == event_id for moment in self.convergence_moments):
            self.convergence_moments.append(convergence)

        return convergence

    def check_convergence(self, event_id: str) -> Optional[ConvergenceMoment]:
        """Public helper mirroring the private convergence check."""

        return self._check_convergence(event_id)

    # --------------------------------------------------------------------- #
    # Aggregate helpers
    # --------------------------------------------------------------------- #
    def can_access_endgame(self) -> bool:
        """Return True once six or more unique facets have been collected."""

        return len(self.collected_facets) >= 6

    def get_missing_facets(self) -> List[SisterFacet]:
        """List facets that have not yet been encountered."""

        return [facet for facet in SisterFacet if facet not in self.collected_facets]

    def get_composite_understanding(self) -> Dict[str, Any]:
        """Summarise progress through the prism system."""

        return {
            "facets_collected": len(self.collected_facets),
            "facets_total": len(SisterFacet),
            "completion_percentage": (
                (len(self.collected_facets) / len(SisterFacet)) * 100
            ),
            "endgame_accessible": self.can_access_endgame(),
            "missing_facets": [facet.value for facet in self.get_missing_facets()],
            "prism_experiences_count": len(self.prism_experiences),
            "convergence_moments_count": len(self.convergence_moments),
            "average_convergence_score": (
                sum(moment.convergence_score for moment in self.convergence_moments)
                / len(self.convergence_moments)
                if self.convergence_moments
                else 0.0
            ),
            "unique_events_interpreted": len(
                {exp.event_id for exp in self.prism_experiences}
            ),
            "veil_proximity_average": (
                sum(exp.veil_proximity for exp in self.prism_experiences)
                / len(self.prism_experiences)
                if self.prism_experiences
                else 0.0
            ),
        }

    def get_facet_insights(self, facet: SisterFacet) -> Dict[str, Any]:
        """Return granular insights for a given facet."""

        experiences = [exp for exp in self.prism_experiences if exp.facet == facet]
        if not experiences:
            return {"collected": False}
        return {
            "collected": True,
            "experience_count": len(experiences),
            "recent_interpretation": experiences[-1].interpretation,
            "average_proximity": sum(exp.veil_proximity for exp in experiences)
            / len(experiences),
            "emotional_tones": [exp.emotional_tone for exp in experiences],
        }


_PRISM_INSTANCE: Optional[SisterPrismSystem] = None


def get_prism_system() -> SisterPrismSystem:
    """Return a shared SisterPrismSystem instance."""

    global _PRISM_INSTANCE
    if _PRISM_INSTANCE is None:
        _PRISM_INSTANCE = SisterPrismSystem()
    return _PRISM_INSTANCE
