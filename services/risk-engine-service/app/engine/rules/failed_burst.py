"""Failed transaction burst detection rule."""

from app.config import settings
from app.engine.rules.base_rule import BaseRule


class FailedBurstRule(BaseRule):
    """Flags accounts with a burst of recent failed transactions.

    Detects potential card testing or brute force patterns.
    In production, queries the DB for recent failed transaction count.
    """

    @property
    def name(self) -> str:
        return "FAILED_BURST"

    def evaluate(self, transaction: dict) -> dict:
        metadata = transaction.get("metadata") or {}
        recent_failures = metadata.get("recent_failed_count", 0)
        threshold = settings.FAILED_BURST_THRESHOLD
        window = settings.FAILED_BURST_WINDOW_MINUTES

        if recent_failures >= threshold:
            score = min(1.0, recent_failures / (threshold * 2))
            return self._result(
                triggered=True,
                score=score,
                reason=(
                    f"Account has {recent_failures} failed transactions "
                    f"in the last {window} minutes (threshold: {threshold})"
                ),
            )

        return self._result(
            triggered=False,
            score=0.0,
            reason=f"Failed transaction count ({recent_failures}) within normal range",
        )
