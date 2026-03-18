"""gRPC client for Transaction Service."""

import grpc
import uuid
from decimal import Decimal
from aegis_shared.generated import risk_engine_pb2_grpc
from aegis_shared.schemas.risk import RiskAssessment

from app.mappers.client_mapper import RiskClientMapper
from app.config import settings
from aegis_shared.utils.logging import get_logger


logger = get_logger("risk_engine_grpc_client")



class RiskEngineClient:
    """"""

    def __init__(self, channel):
        self.channel = channel
        self.stub = risk_engine_pb2_grpc.RiskEngineServiceStub(self.channel)

    
    async def evaluate_risk(
            self,
            transaction_id: uuid.UUID,
            amount: Decimal,
            currency: str,
            sender_id: str,
            receiver_id: str,
            sender_country: str,
            receiver_country: str,
            device_fingerprint: str | None = None,
            ip_address: str | None = None,
            channel: str = "web",
            created_at: str | None = None,
    ) -> RiskAssessment:
        """Evaluate transaction risk via gRPC."""

        logger.info(
            "grpc_evaluate_risk",
            transaction_id=str(transaction_id),
        )

        try:
            request = RiskClientMapper.to_evaluate_proto(
                transaction_id=transaction_id,
                amount=amount,
                currency=currency,
                sender_id=sender_id,
                receiver_id=receiver_id,
                sender_country=sender_country,
                receiver_country=receiver_country,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                channel=channel,
                created_at=created_at,
            )


            response = await self.stub.EvaluateRisk(
                request, timeout=settings.GRPC_TIMEOUT
            )

            return RiskClientMapper.from_evaluate_proto(response)
        
        except grpc.RpcError as e:
            logger.error(
                "grpc_evaluate_risk_failed",
                transaction_id=str(transaction_id),
                code=str(e.code()),
                details=e.details(),
            )
            raise
    
    async def close(self) -> None:
        """Close the gRPC channel. Call during app shutdown."""
            
        await self.channel.close()