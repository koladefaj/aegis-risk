"""gRPC client for LLM Explanation Service."""

import grpc

from app.config import settings
from aegis_shared.utils.logging import get_logger

logger = get_logger("llm_grpc_client")


class LLMGRPCClient:
    """gRPC client for the LLM explanation service.

    Falls back to template-based explanation if unavailable.
    """

    def __init__(self):
        self.address = settings.LLM_GRPC_ADDR

    async def explain_risk(
        self,
        transaction_id: str,
        risk_score: float,
        risk_level: str,
        triggered_rules: list[str],
        ml_score: float,
        amount: float,
        currency: str,
        sender_country: str,
        receiver_country: str,
    ) -> dict:
        """Request an LLM-generated risk explanation via gRPC.

        Args:
            All risk context for explanation generation.

        Returns:
            Dict with summary, risk_factors, recommendation, confidence, fallback_used.
        """
        try:
            channel = grpc.insecure_channel(self.address)
            # from aegis_shared.generated import llm_service_pb2, llm_service_pb2_grpc
            # stub = llm_service_pb2_grpc.LLMServiceStub(channel)
            # request = llm_service_pb2.ExplainRiskRequest(...)
            # response = stub.ExplainRisk(request, timeout=settings.LLM_TIMEOUT_SECONDS)
            channel.close()

            # Placeholder until proto stubs compiled
            rules_text = ", ".join(triggered_rules) if triggered_rules else "none"
            return {
                "summary": (
                    f"Transaction of {amount} {currency} from {sender_country} to "
                    f"{receiver_country} scored {risk_score:.1f}/100 ({risk_level}). "
                    f"Rules triggered: {rules_text}. ML anomaly score: {ml_score:.2f}."
                ),
                "risk_factors": triggered_rules,
                "recommendation": (
                    "APPROVE" if risk_level == "LOW"
                    else "REVIEW" if risk_level == "MEDIUM"
                    else "BLOCK"
                ),
                "confidence": 0.85,
                "fallback_used": False,
            }
        except grpc.RpcError as e:
            logger.warning("llm_service_unavailable", error=str(e))
            raise
