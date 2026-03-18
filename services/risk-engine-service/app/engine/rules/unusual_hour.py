"""Unusual transaction hour detection rule."""

from datetime import datetime

from app.config import settings
from app.engine.rules.base_rule import BaseRule


class UnusualHourRule(BaseRule):
    """Flags transactions occurring during unusual hours.

    Configurable window via UNUSUAL_HOUR_START and UNUSUAL_HOUR_END.
    Default: 22:00 to 05:00 (crosses midnight).

    Handles wrap-around windows correctly:
        start=22, end=5  → flags 22, 23, 0, 1, 2, 3, 4, 5
        start=0,  end=5  → flags 0, 1, 2, 3, 4, 5
    """

    @property
    def name(self) -> str:
        return "UNUSUAL_HOUR"

    def evaluate(self, transaction: dict) -> dict:
        created_at = transaction.get("created_at", "")

        if not created_at:
            return self._result(
                triggered=False,
                score=0.0,
                reason="No timestamp available",
            )

        try:
            if isinstance(created_at, str):
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                ts = created_at

            hour = ts.hour
            start = settings.UNUSUAL_HOUR_START  
            end = settings.UNUSUAL_HOUR_END       

            # handle wrap-around 
            if start > end:
                is_unusual = hour >= start or hour <= end
            else:
                is_unusual = start <= hour <= end

            if is_unusual:
                return self._result(
                    triggered=True,
                    score=0.5,
                    reason=f"Transaction at unusual hour ({hour}:00, window: {start}:00-{end}:00)",
                )

            return self._result(
                triggered=False,
                score=0.0,
                reason=f"Transaction at normal hour ({hour}:00)",
            )

        except (ValueError, TypeError):
            return self._result(
                triggered=False,
                score=0.0,
                reason="Could not parse transaction timestamp",
            )