"""ServiceBridge Advocate: evidence-grounded disability advocacy tooling."""

from .advocate import Advocate
from .models import AdvocacyMode, BenefitLane, EvidenceClass

__all__ = ["Advocate", "AdvocacyMode", "BenefitLane", "EvidenceClass"]
__version__ = "0.1.0"
