"""Account age risk detection rule."""

from app.config import settings
from app.engine.rules.base_rule import BaseRule


class AccountAgeRule(BaseRule):
    """Flags transactions from recently created accounts.

    New accounts (< ACCOUNT_AGE_RISK_DAYS old) are considered higher risk.
    In production, this would query the user profile service.
    """

    @property
    def name(self) -> str:
        return "ACCOUNT_AGE_RISK"

    def evaluate(self, transaction: dict) -> dict:
        metadata = transaction.get("metadata") or {}
        account_age_days = metadata.get("account_age_days")

        if account_age_days is None:
            return self._result(
                triggered=False,
                score=0.0,
                reason="Account age information not available",
            )

        threshold = settings.ACCOUNT_AGE_RISK_DAYS

        if account_age_days < threshold:
            # Higher score for newer accounts
            score = min(1.0, 1.0 - (account_age_days / threshold))
            return self._result(
                triggered=True,
                score=score,
                reason=(
                    f"Account is {account_age_days} days old "
                    f"(risk threshold: {threshold} days)"
                ),
            )

        return self._result(
            triggered=False,
            score=0.0,
            reason=f"Account is {account_age_days} days old (mature account)",
        )
