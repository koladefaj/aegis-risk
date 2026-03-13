"""Transaction gRPC servicer — implements TransactionService RPCs."""

import grpc
from decimal import Decimal

from google.protobuf.json_format import MessageToDict, ParseDict

from app.services.transaction_service import TransactionBusinessService
from app.services.idempotency_service import IdempotencyService
from app.mappers.transaction_mapper import TransactionMapper

from aegis_shared.generated.transaction_pb2 import (
    CreateTransactionResponse,
)
from aegis_shared.generated.common_pb2 import HealthCheckResponse
from aegis_shared.exceptions import DuplicateTransactionError
from aegis_shared.utils.logging import get_logger

logger = get_logger("transaction_servicer")


class TransactionServicer:
    """gRPC servicer implementing the TransactionService."""

    def __init__(self, transaction_service=None, idempotency_service=None):
        self.transaction_service = transaction_service or TransactionBusinessService()
        self.idempotency_service = idempotency_service or IdempotencyService()

    async def CreateTransaction(self, grpc_request, context) -> CreateTransactionResponse:
        """Create a new transaction with idempotency check."""

        idempotency_key = grpc_request.idempotency_key

        logger.info(
            "create_transaction_rpc",
            idempotency_key=idempotency_key,
            amount=f"{str(grpc_request.amount)[:2]}***",
        )

        # 1. Check idempotency cache first
        cached = await self.idempotency_service.check(idempotency_key)
        
        request_data = {
            "amount": str(grpc_request.amount),
            "currency": grpc_request.currency,
            "sender_id": grpc_request.sender_id,
            "receiver_id": grpc_request.receiver_id,
            "sender_country": getattr(grpc_request, "sender_country", ""),
            "receiver_country": getattr(grpc_request, "receiver_country", ""),
        }

        if cached:
            cached_req = cached.get("request", {})
            
            # Strict Idempotency Check (Mismatch detected)
            if cached_req != request_data:
                details = f"Idempotency key {idempotency_key} already used with different parameters"

                logger.warning(
                    "idempotency_conflict",
                    idempotency_key=idempotency_key,
                    original_request=cached_req,
                    attempted_request=request_data,
                )
                await context.abort(grpc.StatusCode.ALREADY_EXISTS, details)
            
            # Perfect duplicate hit - return the cached response
            logger.info("idempotent_duplicate_detected", idempotency_key=idempotency_key)
            response = CreateTransactionResponse()
            return ParseDict(cached["response"], response, ignore_unknown_fields=True)

        # 2. Process new transaction
        try:
            amount = Decimal(str(grpc_request.amount))
        except Exception:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid amount format")

        try:
            result = await self.transaction_service.create(
                idempotency_key=idempotency_key,
                amount=amount,
                currency=grpc_request.currency,
                sender_id=grpc_request.sender_id,
                receiver_id=grpc_request.receiver_id,
                sender_country=grpc_request.sender_country,
                receiver_country=grpc_request.receiver_country,
                device_fingerprint=grpc_request.device_fingerprint,
                ip_address=grpc_request.ip_address,
                channel=grpc_request.channel,
            )

            proto_response = TransactionMapper.to_create_proto(result)

            # Store in idempotency cache
            cache_payload = {
                "request": request_data,
                "response": MessageToDict(proto_response)
            }
            await self.idempotency_service.store(idempotency_key, cache_payload)

            return proto_response
        
        except DuplicateTransactionError as e:
            logger.warning("db_idempotency_conflict", error=e.message,)
            await context.abort(grpc.StatusCode.ALREADY_EXISTS, e.message)

        except ValueError as e:
            logger.warning("invalid_argument", error=str(e))
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

        except (grpc.RpcError, grpc.aio.AbortError):
            raise

        except Exception as e:
            logger.error("create_transaction_failed", error=str(e),)
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred")

    async def GetTransaction(self, grpc_request, context):
        """Retrieve a transaction by ID."""
        transaction_id = grpc_request.transaction_id
        logger.info("get_transaction_rpc", transaction_id=transaction_id)

        try:
            result = await self.transaction_service.get_by_id(transaction_id)
            if result is None:
                await context.abort(grpc.StatusCode.NOT_FOUND, f"Transaction {transaction_id} not found")

            return TransactionMapper.to_get_proto(result)

        except (grpc.RpcError, grpc.aio.AbortError):
            raise

        except Exception as e:
            logger.error("get_transaction_failed", transaction_id=transaction_id, error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred")

    async def UpdateTransactionStatus(self, grpc_request, context):
        """Update a transaction's status atomically."""
        logger.info(
            "update_status_rpc",
            transaction_id=grpc_request.transaction_id,
            new_status=grpc_request.new_status,
        )

        try:
            result = await self.transaction_service.update_status(
                transaction_id=grpc_request.transaction_id,
                new_status=grpc_request.new_status,
                reason=grpc_request.reason,
            )
            return TransactionMapper.to_update_status_proto(result)

        except ValueError as e:
            logger.warning("invalid_status_transition", transaction_id=grpc_request.transaction_id, error=str(e))
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(e))

        except (grpc.RpcError, grpc.aio.AbortError):
            raise

        except Exception as e:
            logger.error("update_status_failed", transaction_id=grpc_request.transaction_id, error=str(e))
            await context.abort(grpc.StatusCode.INTERNAL, "An internal error occurred")

    async def HealthCheck(self, grpc_request, context):
        """Health check endpoint."""
        return HealthCheckResponse(
            status="ok",
            service_name="transaction-service",
            version="1.0.0",
        )