"""Risk scoring orchestrator — combines rule-based and ML results.

LLM explanation is NOT called inline — it's too slow for the <300ms SLA.
The orchestrator returns a RiskAssessment immediately after ML scoring.
LLM explanation is triggered async via SQS and delivered via webhook.
"""

import time
import uuid
from datetime import datetime, UTC
from decimal import Decimal

from app.db.session import get_session

from app.config import settings
from app.engine.scorer import RiskScorer
from app.engine.rules import get_all_rules
from app.grpc_clients.ml_client import MLGRPCClient
from app.repositories.account_profile_repo import AccountProfileRepository
from aegis_shared.generated.risk_engine_pb2 import RuleFlagResult
from aegis_shared.generated.transaction_pb2 import RiskFactor
from aegis_shared.enums import RiskLevel, RiskDecision
from aegis_shared.schemas.risk import RiskAssessment, RuleFlagResult
from aegis_shared.utils.logging import get_logger

logger = get_logger("orchestrator")


class RiskOrchestrator:
    """Orchestrates the synchronous risk evaluation pipeline.

    Flow:
        1. Load account profile from DB (or create if new account)
        2. Enrich transaction dict with behavioural features
        3. Run all rule-based checks
        4. Call ML service for anomaly score (with fallback)
        5. Calculate combined score → RiskLevel → RiskDecision
        6. Return RiskAssessment immediately (<300ms)

    LLM explanation is NOT part of this flow — it runs async via SQS
    consumer and is delivered to the bank via webhook.
    """

    def __init__(self, scorer: RiskScorer, ml_client: MLGRPCClient):
        self.rules = get_all_rules()
        self.scorer = scorer
        self.ml_client = ml_client

    async def evaluate(self, transaction_data: dict) -> RiskAssessment:
        """Run the synchronous risk evaluation pipeline.

        Args:
            transaction_data: Transaction fields from EvaluateRiskRequest.

        Returns:
            RiskAssessment — returned immediately to transaction-service.
        """
        start_time = time.perf_counter()
        transaction_id = transaction_data.get("transaction_id", "unknown")
        sender_id = transaction_data.get("sender_id", "")
        amount = Decimal(str(transaction_data.get("amount", 0)))

        logger.info("risk_evaluation_started", transaction_id=transaction_id)

        # Step 1: Load account profile
        async with get_session() as session:
            profile_repo = AccountProfileRepository(session)
            profile = await profile_repo.get_or_create(sender_id)

        # Step 2: Enrich transaction with behavioural features
        # Rules read from transaction["metadata"] — populated here from profile
        transaction_data["metadata"] = {
            "account_age_days": profile.account_age_days,
            "recent_transaction_count": profile.txn_count_1h,
            "recent_failed_count": profile.blocked_txn_count,
            "known_devices": profile.known_device_fingerprints or [],
            "is_new_device": profile.is_new_device(
                transaction_data.get("device_fingerprint", "")
            ),
            "is_new_receiver": profile.is_new_receiver(
                transaction_data.get("receiver_id", "")
            ),
            "known_receivers": profile.known_receiver_ids or [],
            "fraud_txn_count": profile.fraud_txn_count,
            "is_high_risk_account": profile.is_high_risk,
        }

        # Step 3: Run all rules
        rule_results = []
        for rule in self.rules:
            try:
                result = rule.evaluate(transaction_data)
                rule_results.append(result)
            except Exception as e:
                logger.error(
                    "rule_evaluation_failed",
                    rule=rule.name,
                    error=str(e),
                    transaction_id=transaction_id,
                )
                rule_results.append({
                    "rule": rule.name,
                    "triggered": False,
                    "score": 0.0,
                    "reason": f"Rule evaluation failed: {str(e)}",
                })

        rule_score = self.scorer.calculate_rule_score(rule_results)

        # Step 4: ML anomaly score (with fallback)
        ml_result = await self._get_ml_score(transaction_data, profile)

        # Step 5: Calculate final score → level → decision
        final_score = self.scorer.calculate_final_score(
            rule_score=rule_score,
            ml_score=ml_result["anomaly_score"],
            rule_weight=settings.RULE_SCORE_WEIGHT,
            ml_weight=settings.ML_SCORE_WEIGHT,
        )

        risk_level = self.scorer.categorize_risk(final_score)
        decision = self.scorer.make_decision(risk_level)

        # Step 6: Build risk factors list for explanation — triggered rules + ML anomaly
        risk_factors = [
            {
                "factor": r["rule"],
                "severity": self._score_to_severity(r["score"]),
                "detail": r["reason"],
            }
            for r in rule_results
            if r.get("triggered", False)
        ]

        processing_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "risk_evaluation_completed",
            transaction_id=transaction_id,
            risk_score=round(final_score, 2),
            risk_level=risk_level.value,
            decision=decision.value,
            processing_time_ms=round(processing_time_ms, 2),
            rules_triggered=len(risk_factors),
            ml_fallback=ml_result.get("fallback_used", False),
        )

        return RiskAssessment(
            transaction_id=transaction_id,
            decision=decision,
            risk_score=round(final_score / 100, 4),  # normalize to 0–1
            risk_level=risk_level,
            confidence=self._score_to_confidence(final_score),
            risk_factors=risk_factors,
            processing_time_ms=round(processing_time_ms, 2),
            model_version=ml_result.get("model_version", "1.0.0"),
        )

    async def _get_ml_score(self, transaction_data: dict, profile) -> dict:
        """Get ML anomaly score with graceful fallback.

        Passes both raw transaction fields and derived profile features
        to ml-service so it has the full feature vector.
        """
        try:
            feature_vector = profile.to_feature_dict(
                current_amount=Decimal(str(transaction_data.get("amount", 0))),
                receiver_id=transaction_data.get("receiver_id", ""),
                device_fingerprint=transaction_data.get("device_fingerprint", ""),
            )
            return await self.ml_client.score_transaction(
                transaction_data=transaction_data,
                features=feature_vector,
            )
        except Exception as e:
            logger.warning(
                "ml_service_fallback",
                error=str(e),
                transaction_id=transaction_data.get("transaction_id"),
            )
            return {
                "anomaly_score": 0.5,   # neutral — don't bias the decision
                "model_version": "fallback",
                "fallback_used": True,
            }
        
    async def _get_llm_explanation(self, transaction_id, risk_score, risk_level, triggered_rules, ml_score, transaction_data) -> str:
        """
        Placeholder that safely ignores extra arguments like 
        transaction_id or risk_score until we actually need them.
        """

        tx_id = transaction_id
        
        return {
            "summary": f"LLM placeholder analysis for transaction {tx_id} completed.",
            "risk_factors": ["Velocity check triggered"],
            "recommendation": "Manual Review",
            "confidence": 0.85,
            "model": "ollama-llama3",
            "latency_ms": 120.5,
            "fallback_used": False
        }

    @staticmethod
    def _score_to_severity(score: float) -> str:
        """Convert a rule score (0–1) to a severity label."""
        if score >= 0.8:
            return "HIGH"
        if score >= 0.5:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _score_to_confidence(final_score: float) -> str:
        """Confidence is high when score is clearly in one zone."""
        # High confidence when far from thresholds
        if final_score <= 25 or final_score >= 85:
            return "HIGH"
        # Low confidence near decision boundaries
        if 35 <= final_score <= 55:
            return "LOW"
        return "MEDIUM"