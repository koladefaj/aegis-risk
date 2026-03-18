"""Geo-location mismatch detection rule."""

from app.engine.rules.base_rule import BaseRule

# High-risk country pairs
HIGH_RISK_CORRIDORS = {
    ("US", "NG"), ("US", "GH"), ("GB", "NG"),
    ("US", "RU"), ("GB", "RU"), ("US", "KP"),
}


class GeoMismatchRule(BaseRule):
    """Flags transactions where sender and receiver are in different countries,
    especially high-risk corridors.

    Score:
    - Same country: 0.0
    - Different country: 0.3
    - High-risk corridor: 0.8
    """

    @property
    def name(self) -> str:
        return "GEO_MISMATCH"

    def evaluate(self, transaction: dict) -> dict:
        sender_country = transaction.get("sender_country", "").upper()
        receiver_country = transaction.get("receiver_country", "").upper()

        if not sender_country or not receiver_country:
            return self._result(
                triggered=False,
                score=0.0,
                reason="Country information not available",
            )

        # Same country — no risk
        if sender_country == receiver_country:
            return self._result(
                triggered=False,
                score=0.0,
                reason=f"Domestic transaction ({sender_country})",
            )

        # Check high-risk corridor
        pair = (sender_country, receiver_country)
        reverse_pair = (receiver_country, sender_country)

        if pair in HIGH_RISK_CORRIDORS or reverse_pair in HIGH_RISK_CORRIDORS:
            return self._result(
                triggered=True,
                score=0.8,
                reason=(
                    f"High-risk geographic corridor: "
                    f"{sender_country} → {receiver_country}"
                ),
            )

        # Cross-border but not high-risk
        return self._result(
            triggered=True,
            score=0.3,
            reason=f"Cross-border transaction: {sender_country} → {receiver_country}",
        )
