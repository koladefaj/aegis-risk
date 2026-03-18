"""Risk Engine gRPC servicer."""
import grpc
from app.engine.orchestrator import RiskOrchestrator
from aegis_shared.generated.common_pb2 import HealthCheckResponse
from aegis_shared.generated.risk_engine_pb2 import (
    GetRiskResultResponse,
    EvaluateRiskResponse
)

from app.mappers.risk_mapper import RiskServicerMapper
from aegis_shared.utils.logging import get_logger

logger = get_logger("risk_engine_servicer")


class RiskEngineServicer:
    """gRPC servicer for the Risk Engine.

    Provides synchronous risk evaluation and result lookup.
    """

    def __init__(self, orchestrator: RiskOrchestrator):
        self.orchestrator = orchestrator

    async def EvaluateRisk(self, grpc_request, context):
        """Synchronous risk evaluation RPC (for direct gRPC calls)."""

        transaction_id = grpc_request.transaction_id

        logger.info(
            "evaluate_risk_rpc",
            transaction_id=transaction_id,
        )

        try:
            result = await self.orchestrator.evaluate(
                transaction_data = {
                    "transaction_id": transaction_id,
                    "amount": grpc_request.amount,
                    "currency": grpc_request.currency,
                    "sender_id": grpc_request.sender_id,
                    "receiver_id": grpc_request.receiver_id,
                    "sender_country": grpc_request.sender_country,
                    "receiver_country": grpc_request.receiver_country,
                    "device_fingerprint": grpc_request.device_fingerprint,
                    "ip_address": grpc_request.ip_address,
                    "channel": grpc_request.channel,
                    "created_at": grpc_request.created_at,
                },
            )
            return RiskServicerMapper.to_create_proto(result)
        
        except ValueError as e:
            logger.warning(
                "evaluate_risk_invalid_argument",
                transaction_id=transaction_id,
                error=str(e),
            )
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return EvaluateRiskResponse()  # Return empty response on invalid argument
        
        except Exception as e:
            logger.error(
                "evaluate_risk_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return EvaluateRiskResponse()  # Return empty response on failure

    async def GetRiskResult(self, request, context):
        """Retrieve a stored risk evaluation result."""
        transaction_id = request.transaction_id
        logger.info("get_risk_result_rpc", transaction_id=transaction_id)

        try:
            result = await self.orchestrator.get_result(transaction_id)

            if result is None:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"Risk result for {transaction_id} not found")
                return GetRiskResultResponse()

            return RiskServicerMapper.to_get_result_proto(result)

        except Exception as e:
            logger.error(
                "get_risk_result_failed",
                transaction_id=transaction_id,
                error=str(e),
            )
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise

    async def StreamExplanation(self, request, context):
        raise NotImplementedError("StreamExplanation not implemented yet")

    async def HealthCheck(self, request, context):
        """Health check endpoint."""
        return HealthCheckResponse(
            status="ok",
            service_name="risk-engine-service",
            version="1.0.0",
        )
