""" gRPC Transaction Servicer Mapper from proto to pydantic/json """

from datetime import datetime
from uuid import UUID
from decimal import Decimal
from aegis_shared.generated.transaction_pb2 import (
    CreateTransactionResponse,
    GetTransactionResponse,
    UpdateStatusResponse
)

class TransactionMapper:
    """Centralized mapping logic between Business Models/ORMs and Protobuf."""

    @staticmethod
    def _format_field(value):
        """Helper to handle type conversion for Protobuf compatibility."""
        if value is None:
            return ""
        if isinstance(value, (UUID, Decimal)):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if hasattr(value, "value"):  # Handle Enums
            return str(value.value)
        return value

    @classmethod
    def to_create_proto(cls, internal_obj) -> CreateTransactionResponse:
        # Convert ORM to dict if necessary, otherwise handle dict/pydantic
        data = internal_obj.__dict__ if hasattr(internal_obj, "__dict__") else internal_obj
        
        return CreateTransactionResponse(
            transaction_id=cls._format_field(data.get("transaction_id")),
            idempotency_key=data.get("idempotency_key"),
            amount=cls._format_field(data.get("amount")),
            currency=data.get("currency"),
            sender_id=data.get("sender_id"),
            receiver_id=data.get("receiver_id"),
            status=cls._format_field(data.get("status")),
            created_at=cls._format_field(data.get("created_at")),
            already_existed=bool(data.get("already_existed", False)),
            sender_country=data.get("sender_country", ""),
            receiver_country=data.get("receiver_country", "")
        )

    @classmethod
    def to_get_proto(cls, internal_obj) -> GetTransactionResponse:
        data = internal_obj.__dict__ if hasattr(internal_obj, "__dict__") else internal_obj
        
        return GetTransactionResponse(
            transaction_id=cls._format_field(data.get("transaction_id")),
            idempotency_key=data.get("idempotency_key"),
            amount=cls._format_field(data.get("amount")),
            currency=data.get("currency"),
            sender_id=data.get("sender_id"),
            receiver_id=data.get("receiver_id"),
            sender_country=data.get("sender_country", ""),
            receiver_country=data.get("receiver_country", ""),
            status=cls._format_field(data.get("status")),
            created_at=cls._format_field(data.get("created_at")),
            updated_at=cls._format_field(data.get("updated_at"))
        )

    @staticmethod
    def to_update_status_proto(result_dict: dict) -> UpdateStatusResponse:
        # result_dict usually comes directly from the repo's update_status method
        return UpdateStatusResponse(
            transaction_id=str(result_dict.get("transaction_id")),
            previous_status=str(result_dict.get("previous_status")),
            new_status=str(result_dict.get("new_status")),
            success=bool(result_dict.get("success"))
        )