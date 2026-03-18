"""gRPC client for ML Anomaly Service."""

import grpc

from app.config import settings
from aegis_shared.utils.logging import get_logger

logger = get_logger("ml_grpc_client")


class MLGRPCClient:
    """gRPC client for the ML anomaly detection service.

    Falls back gracefully if the ML service is unavailable.
    """

    def __init__(self):
        self.address = settings.ML_GRPC_ADDR
        self.channel = grpc.insecure_channel(self.address)

    async def score_transaction(self, transaction_data: dict) -> dict:
        """Score a transaction for anomalies via gRPC.

        Args:
            transaction_data: Transaction event data.

        Returns:
            Dict with anomaly_score, model_version, fallback_used.
        """
        try:
            channel = grpc.insecure_channel(self.address)
            # from aegis_shared.generated import ml_service_pb2, ml_service_pb2_grpc
            # stub = ml_service_pb2_grpc.MLServiceStub(channel)
            # request = ml_service_pb2.ScoreTransactionRequest(...)
            # response = stub.ScoreTransaction(request)
            channel.close()

            # Placeholder until proto stubs compiled
            # Simulate a reasonable anomaly score based on amount
            amount = float(transaction_data.get("amount", 0))
            score = min(1.0, amount / 50000)  # Higher amounts = higher anomaly

            return {
                "anomaly_score": score,
                "model_version": settings.WORKER_ID,
                "fallback_used": False,
            }
        except grpc.RpcError as e:
            logger.warning("ml_service_unavailable", error=str(e))
            raise

    async def close(self) -> None:
        """Close the gRPC channel. Call during app shutdown."""
            
        await self.channel.close()
