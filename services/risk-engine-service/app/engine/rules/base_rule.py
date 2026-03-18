"""Base rule interface for all risk detection rules."""

from abc import ABC, abstractmethod


class BaseRule(ABC):
    """Abstract base class for risk detection rules.

    All rules must implement the evaluate() method and provide a name.
    Rules are config-driven — thresholds are loaded from settings, not hardcoded.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique rule identifier."""
        ...

    @abstractmethod
    def evaluate(self, transaction: dict) -> dict:
        """Evaluate the transaction against this rule.

        Args:
            transaction: Transaction event data dict.

        Returns:
            Dict with keys:
                - rule: str (rule name)
                - triggered: bool
                - score: float (0.0 to 1.0)
                - reason: str (human-readable explanation)
        """
        ...

    def _result(self, triggered: bool, score: float, reason: str) -> dict:
        """Build a standardized rule result.

        Args:
            triggered: Whether the rule flagged the transaction.
            score: Risk contribution score (0.0 to 1.0).
            reason: Human-readable explanation.

        Returns:
            Standardized result dict.
        """
        return {
            "rule": self.name,
            "triggered": triggered,
            "score": score,
            "reason": reason,
        }
