"""
Core gameplay primitives for the Veil/Lyssandra systems.

The original `.20_Veil` tree shipped a large amount of narrative content but no
import-friendly modules.  This package extracts the mechanically useful pieces
so production services can depend on a small, well-tested surface.
"""

from . import assets, db, voice
from .prism import ConvergenceMoment, PrismExperience, SisterFacet, SisterPrismSystem
from .revelation import (
    OrderDevotion,
    PaymentType,
    RevelationEvent,
    RevelationSystem,
    SisterTrust,
)

__all__ = [
    "ConvergenceMoment",
    "PrismExperience",
    "SisterFacet",
    "SisterPrismSystem",
    "OrderDevotion",
    "PaymentType",
    "RevelationEvent",
    "RevelationSystem",
    "SisterTrust",
    "assets",
    "db",
    "voice",
]
