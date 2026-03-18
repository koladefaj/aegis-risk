"""Risk score calculation and categorization."""

from aegis_shared.enums import RiskLevel, RiskDecision
from aegis_shared.utils.logging import get_logger

logger = get_logger("scorer")


class RiskScorer:
    """Calculates final risk scores from rule and ML inputs.

    Score formula:
        final_score = (rule_score * rule_weight) + (ml_score * 100 * ml_weight)

    Risk categories:
        LOW:      0–40
        MEDIUM:   41–70
        HIGH:     71–90
        CRITICAL: 91–100
    """

    def calculate_rule_score(self, rule_results: list[dict]) -> float:
        """Calculate aggregate score from rule evaluations.

        Only triggered rules contribute to the score — untriggered rules
        returning score=0.0 don't dilute the aggregate.

        Args:
            rule_results: List of rule evaluation result dicts.

        Returns:
            Aggregate rule score (0–100).
        """
        if not rule_results:
            return 0.0

        triggered = [r for r in rule_results if r.get("triggered", False)]

        if not triggered:
            return 0.0

        # Sum scores from triggered rules only
        total_score = sum(r.get("score", 0.0) for r in triggered)

        # Normalize against total possible (all rules triggered at max score)
        max_possible = len(rule_results)
        normalized = (total_score / max_possible) * 100

        return min(100.0, max(0.0, normalized))

    def calculate_final_score(
        self,
        rule_score: float,
        ml_score: float,
        rule_weight: float = 0.6,
        ml_weight: float = 0.4,
    ) -> float:
        """Calculate the weighted final risk score.

        Args:
            rule_score: Rule-based score (0–100).
            ml_score: ML anomaly score (0–1).
            rule_weight: Weight for rule score (should sum to 1.0 with ml_weight).
            ml_weight: Weight for ML score.

        Returns:
            Final risk score (0–100).
        """
        if abs((rule_weight + ml_weight) - 1.0) > 0.001:
            logger.warning(
                "score_weights_dont_sum_to_one",
                rule_weight=rule_weight,
                ml_weight=ml_weight,
            )

        ml_contribution = ml_score * 100 * ml_weight
        rule_contribution = rule_score * rule_weight
        final = rule_contribution + ml_contribution

        return min(100.0, max(0.0, final))

    def categorize_risk(self, score: float) -> RiskLevel:
        """Categorize a risk score into LOW/MEDIUM/HIGH/CRITICAL.

        Args:
            score: Risk score (0–100).

        Returns:
            RiskLevel enum value.
        """
        if score >= 91:
            return RiskLevel.CRITICAL
        if score >= 71:
            return RiskLevel.HIGH
        if score >= 41:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def make_decision(self, risk_level: RiskLevel) -> RiskDecision:
        """Map a RiskLevel to a RiskDecision.

        Uses enum classmethod — single source of truth for thresholds.
        """
        return {
            RiskLevel.LOW:      RiskDecision.APPROVE,
            RiskLevel.MEDIUM:   RiskDecision.REVIEW,
            RiskLevel.HIGH:     RiskDecision.BLOCK,
            RiskLevel.CRITICAL: RiskDecision.BLOCK,
        }.get(risk_level, RiskDecision.REVIEW)