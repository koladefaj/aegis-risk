""" gRPC Client mapper to from proto to pydantic/json """

import uuid
from decimal import Decimal
from datetime import datetime
from fastapi import Request
from aegis_shared.generated import transaction_pb2
from aegis_shared.generated.common_pb2 import RequestMetadata
from aegis_shared.schemas.transaction import TransactionAccepted, TransactionResponse, TransactionCreate, TransactionUpdate

class TransactionClientMapper:
    """Maps between Pydantic schemas and gRPC Messages for the Client."""

    # --- Outgoing (Request) Mappers ---

    @staticmethod
    def to_create_proto(
        schema: TransactionCreate, 
        client_id: str, 
        request: Request,
    ) -> transaction_pb2.CreateTransactionRequest:
        
        # Centralize the Decimal formatting logic
        amount_str = str(schema.amount.quantize(Decimal("0.01")))
        
        return transaction_pb2.CreateTransactionRequest(
            metadata=RequestMetadata(
                correlation_id=request.state.correlation_id,
                client_id=client_id,
            ),
            idempotency_key=schema.idempotency_key or str(uuid.uuid4()),
            amount=amount_str,
            currency=schema.currency,
            sender_id=schema.sender_id,
            receiver_id=schema.receiver_id,
            sender_country=schema.sender_country,
            receiver_country=schema.receiver_country,
            device_fingerprint=schema.device_fingerprint or "",
            ip_address=getattr(request.client, "host", "unknown") or "",
            channel=schema.channel,
        )
    
    @staticmethod
    def to_get_proto(request: Request, client_id: str, transaction_id: uuid.UUID) -> transaction_pb2.GetTransactionRequest:
        return transaction_pb2.GetTransactionRequest(
            metadata=RequestMetadata(
                correlation_id=request.state.correlation_id,
                client_id=client_id,
            ),
            transaction_id=str(transaction_id),
        )
    
    @staticmethod
    def to_update_proto(request: Request, transaction_id, new_status, reason) -> transaction_pb2.UpdateStatusRequest:
        return transaction_pb2.UpdateStatusRequest(
            metadata=RequestMetadata(
               correlation_id=request.state.correlation_id,
            ),
            transaction_id=str(transaction_id),
            new_status=new_status,
            reason=reason
        )
    
    # --- Incoming (Response) Mappers ---

    @staticmethod
    def from_create_proto(proto: transaction_pb2.CreateTransactionResponse) -> TransactionAccepted:
        return TransactionAccepted(
            transaction_id=uuid.UUID(proto.transaction_id),
            idempotency_key=proto.idempotency_key,
            amount=Decimal(proto.amount),
            currency=proto.currency,
            sender_id=proto.sender_id,
            receiver_id=proto.receiver_id,
            sender_country=proto.sender_country,
            receiver_country=proto.receiver_country,
            status=proto.status,
            created_at=datetime.fromisoformat(proto.created_at),
            already_existed=proto.already_existed,
        )
    
    @staticmethod
    def from_get_proto(proto: transaction_pb2.GetTransactionResponse) -> TransactionResponse:
        return TransactionResponse(
            transaction_id=uuid.UUID(proto.transaction_id),
            idempotency_key=proto.idempotency_key,
            amount=Decimal(proto.amount),
            currency=proto.currency,
            sender_id=proto.sender_id,
            receiver_id=proto.receiver_id,
            sender_country=proto.sender_country,
            receiver_country=proto.receiver_country,
            status=proto.status,
            created_at=datetime.fromisoformat(proto.created_at),
            updated_at=datetime.fromisoformat(proto.updated_at)
            if proto.updated_at else None,
        )
    
    @staticmethod
    def from_update_proto(proto: transaction_pb2.UpdateStatusResponse) -> TransactionUpdate:
        return TransactionUpdate(
            transaction_id=uuid.UUID(proto.transaction_id),
            previous_status=proto.previous_status,
            new_status=proto.new_status,
            success=proto.success,
        ) 