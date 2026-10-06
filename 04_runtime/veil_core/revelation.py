"""Order-to-Sister revelation progression system."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class PaymentType(Enum):
    """How the player paid an Order."""

    COIN = "coin"
    FAVOR = "favor"
    SELF = "self"


@dataclass
class OrderDevotion:
    """Publicly visible devotion metrics."""

    order_id: str
    usage_count: int = 0
    coin_payments: int = 0
    favor_payments: int = 0
    self_payments: int = 0
    last_interaction: Optional[str] = None
    devotion_score: float = 0.0


@dataclass
class SisterTrust:
    """Hidden Sister trust meter."""

    sister_id: str
    trust_level: int = 0
    sincere_interactions: int = 0
    confessions_offered: int = 0
    quality_score: float = 0.0
    last_interaction: Optional[str] = None
    betrayals: int = 0


@dataclass
class RevelationEvent:
    """Audit record for a triggered revelation."""

    sister_id: str
    order_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    devotion_score: float = 0.0
    trust_level: int = 0
    veil_proximity: float = 0.0
    dialogue_unlocked: str = ""


class RevelationSystem:
    """Dual-meter revelation tracker."""

    def __init__(self) -> None:
        self.order_devotion: Dict[str, OrderDevotion] = {}
        self.sister_trust: Dict[str, SisterTrust] = {}
        self.revelations_unlocked: List[RevelationEvent] = []
        self.sister_order_map = {
            "seamwright": "seraphyne_vale",
            "clockmender": "valeria_syn",
            "bookbinder": "lilithrae_vex",
            "bathhouse": "revana_morn",
            "tea_host": "isolde_ryn",
            "glassblower": "caldrith_synn",
            "launderer": "thalia_vex",
            "night_watch": "morrigan_ash",
            "cartographer": "nyxaria_vell",
        }

    # ------------------------------------------------------------------ #
    # Interaction recording
    # ------------------------------------------------------------------ #
    def record_order_interaction(
        self,
        *,
        order_id: str,
        payment_type: PaymentType,
        sincerity_score: float = 0.5,
        interaction_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Update devotion and hidden trust after an interaction."""

        devotion = self.order_devotion.setdefault(order_id, OrderDevotion(order_id))
        devotion.usage_count += 1

        if payment_type == PaymentType.COIN:
            devotion.coin_payments += 1
        elif payment_type == PaymentType.FAVOR:
            devotion.favor_payments += 1
        else:
            devotion.self_payments += 1

        devotion.last_interaction = datetime.now().isoformat()
        devotion.devotion_score = self._calculate_devotion_score(devotion)

        sister_id = self._get_sister_for_order(order_id)
        trust_change = self._update_sister_trust(
            sister_id=sister_id,
            payment_type=payment_type,
            sincerity_score=sincerity_score,
            details=interaction_details,
        )

        return {
            "order_id": order_id,
            "devotion_score": devotion.devotion_score,
            "trust_change": trust_change,
            "payment_type": payment_type.value,
            "sincere": sincerity_score > 0.7,
        }

    def _calculate_devotion_score(self, devotion: OrderDevotion) -> float:
        """Weighted devotion score favouring self-sacrifice."""

        weighted = (
            devotion.self_payments * 10
            + devotion.favor_payments * 5
            + devotion.coin_payments * 1
        )
        return min(100.0, float(weighted))

    def _update_sister_trust(
        self,
        *,
        sister_id: str,
        payment_type: PaymentType,
        sincerity_score: float,
        details: Optional[Dict[str, Any]],
    ) -> int:
        """Adjust hidden Sister trust based on interaction quality."""

        trust = self.sister_trust.setdefault(sister_id, SisterTrust(sister_id))
        previous = trust.trust_level

        if payment_type == PaymentType.SELF and sincerity_score > 0.7:
            trust_gain = 15
            trust.sincere_interactions += 1
            trust.confessions_offered += 1
        elif payment_type == PaymentType.FAVOR and sincerity_score > 0.5:
            trust_gain = 10
            trust.sincere_interactions += 1
        elif payment_type == PaymentType.COIN:
            trust_gain = 2
        else:
            trust_gain = 0

        trust_gain = int(trust_gain * sincerity_score)
        trust.trust_level = min(100, trust.trust_level + trust_gain)

        total_interactions = trust.sincere_interactions + trust.betrayals + 1
        trust.quality_score = (
            (trust.quality_score * (total_interactions - 1)) + sincerity_score
        ) / total_interactions
        trust.last_interaction = datetime.now().isoformat()

        return trust.trust_level - previous

    # ------------------------------------------------------------------ #
    # Threshold checks
    # ------------------------------------------------------------------ #
    def check_revelation_threshold(
        self,
        *,
        order_id: str,
        veil_proximity: float,
    ) -> Dict[str, Any]:
        """Return whether the revelation requirements are satisfied."""

        sister_id = self._get_sister_for_order(order_id)
        if not sister_id:
            return {"can_reveal": False, "reason": "Invalid order"}

        devotion = self.order_devotion.get(order_id)
        trust = self.sister_trust.get(sister_id)

        if not devotion or not trust:
            return {
                "can_reveal": False,
                "reason": "Insufficient interaction",
                "requirements": {
                    "devotion_met": False,
                    "trust_met": False,
                    "proximity_met": False,
                },
            }

        devotion_met = devotion.devotion_score >= 50.0
        trust_met = trust.trust_level >= 60
        proximity_met = veil_proximity >= 0.6

        return {
            "can_reveal": devotion_met and trust_met and proximity_met,
            "requirements": {
                "devotion_met": devotion_met,
                "devotion_score": devotion.devotion_score,
                "devotion_required": 50.0,
                "trust_met": trust_met,
                "trust_level": trust.trust_level,
                "trust_required": 60,
                "proximity_met": proximity_met,
                "proximity_current": veil_proximity,
                "proximity_required": 0.6,
            },
            "sister_id": sister_id,
        }

    def trigger_revelation(
        self,
        *,
        sister_id: str,
        veil_proximity: float,
    ) -> Dict[str, Any]:
        """Record a revelation if it has not already occurred."""

        if any(event.sister_id == sister_id for event in self.revelations_unlocked):
            return {"success": False, "reason": "Already revealed", "sister_id": sister_id}

        order_id = self._get_order_for_sister(sister_id)
        devotion = self.order_devotion.get(order_id) if order_id else None
        trust = self.sister_trust.get(sister_id)

        if not devotion or not trust:
            return {"success": False, "reason": "Insufficient data"}

        revelation = RevelationEvent(
            sister_id=sister_id,
            order_id=order_id,
            devotion_score=devotion.devotion_score,
            trust_level=trust.trust_level,
            veil_proximity=veil_proximity,
            dialogue_unlocked=f"{sister_id}_revelation",
        )
        self.revelations_unlocked.append(revelation)

        return {
            "success": True,
            "sister_id": sister_id,
            "order_id": order_id,
            "revelation_event": revelation,
            "dialogue_unlocked": revelation.dialogue_unlocked,
            "timestamp": revelation.timestamp,
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _get_sister_for_order(self, order_id: str) -> Optional[str]:
        return self.sister_order_map.get(order_id)

    def _get_order_for_sister(self, sister_id: str) -> Optional[str]:
        inverse = {sister: order for order, sister in self.sister_order_map.items()}
        return inverse.get(sister_id)
