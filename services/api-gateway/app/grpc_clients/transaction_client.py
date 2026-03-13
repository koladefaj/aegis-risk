"""gRPC client for Transaction Service."""

import grpc
import uuid
from fastapi import Request
from aegis_shared.generated import transaction_pb2_grpc
from aegis_shared.schemas.transaction import (
    TransactionAccepted,
    TransactionResponse,
    TransactionUpdate,
    TransactionCreate,
)

from app.mappers.client_mapper import TransactionClientMapper
from app.config import settings
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_grpc_client")


class TransactionGRPCClient:
    """
    Client for communicating with the Transaction gRPC service.
    """

    def __init__(self):
        if settings.GRPC_USE_TLS:
            credentials = grpc.ssl_channel_credentials()
            self.channel = grpc.aio.secure_channel(
                settings.TRANSACTION_GRPC_ADDR,
                credentials
            )
        else:
            self.channel = grpc.aio.insecure_channel(
                settings.TRANSACTION_GRPC_ADDR
            )
        self.stub = transaction_pb2_grpc.TransactionServiceStub(self.channel)

    async def create_transaction(
        self,
        transaction: TransactionCreate,
        client_id: str,
        request: Request,
    ) -> TransactionAccepted:
        """Create a new transaction via gRPC."""

        logger.info(
            "grpc_create_transaction",
        )

        try:
    
            request = TransactionClientMapper.to_create_proto(
                schema=transaction,
                client_id=client_id,
                request=request,
            )

            response = await self.stub.CreateTransaction(
                request, timeout=settings.GRPC_TIMEOUT
            )

            return TransactionClientMapper.from_create_proto(response)

        except grpc.RpcError as e:
            logger.error(
                "grpc_create_transaction_failed",
                code=str(e.code()),
                details=e.details(),
            )
            raise

    async def get_transaction(
        self,
        transaction_id: uuid.UUID,
        client_id: str,
        request: Request,
    ) -> TransactionResponse | None:
        """Get transaction details via gRPC."""

        logger.info(
            "grpc_get_transaction",
            transaction_id=transaction_id,
        )

        try:
            req = TransactionClientMapper.to_get_proto(
                client_id=client_id,
                transaction_id=transaction_id,
                request=request,
            )

            response = await self.stub.GetTransaction(
                req, timeout=settings.GRPC_TIMEOUT
            )

            return TransactionClientMapper.from_get_proto(response)


        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                return None
            logger.error(
                "grpc_get_transaction_failed",
                code=str(e.code()),
                details=e.details(),
                transaction_id=transaction_id,
            )
            raise

    async def update_status(
        self,
        request: Request,
        transaction_id: uuid.UUID,
        new_status: str,
        reason: str = "",
    ) -> TransactionUpdate:
        """Update transaction status via gRPC."""

        logger.info(
            "grpc_update_status",
            transaction_id=transaction_id,
            new_status=new_status,
        )

        try:
            req = TransactionClientMapper.to_update_proto(
                request=request,
                transaction_id=transaction_id,
                new_status=new_status,
                reason=reason,   
            )

            response = await self.stub.UpdateTransactionStatus(
                req, timeout=settings.GRPC_TIMEOUT
            )

            return TransactionClientMapper.from_update_proto(response)

        except grpc.RpcError as e:
            logger.error(
                "grpc_update_status_failed",
                code=str(e.code()),
                details=e.details(),
                transaction_id=transaction_id,
            )
            raise

    async def close(self) -> None:
        """Close the gRPC channel. Call during app shutdown."""
        
        await self.channel.close()