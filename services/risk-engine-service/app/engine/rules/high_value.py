"""High-value transaction detection rule."""

from app.config import settings
from app.engine.rules.base_rule import BaseRule


class HighValueRule(BaseRule):
    """Flags transactions above a configurable amount threshold.

    Threshold is loaded from settings.HIGH_VALUE_THRESHOLD.
    Score scales linearly from 0.5 at threshold to 1.0 at 5x threshold.
    """

    @property
    def name(self) -> str:
        return "HIGH_VALUE"

    def evaluate(self, transaction: dict) -> dict:
        amount = float(transaction.get("amount", 0))
        threshold = settings.HIGH_VALUE_THRESHOLD

        if amount >= threshold:
            # Scale score: 0.5 at threshold, 1.0 at 5x threshold
            ratio = min(amount / threshold, 5.0)
            score = min(1.0, 0.5 + (ratio - 1.0) * 0.125)

            return self._result(
                triggered=True,
                score=score,
                reason=f"Transaction amount ${amount:,.2f} exceeds threshold ${threshold:,.2f}",
            )

        return self._result(
            triggered=False,
            score=0.0,
            reason=f"Amount ${amount:,.2f} is within normal range",
        )
