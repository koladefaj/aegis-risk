"""gRPC Transaction Servicer Mapper from proto to pydantic/json"""

from datetime import datetime
from uuid import UUID
from decimal import Decimal

from aegis_shared.generated.transaction_pb2 import (
    CreateTransactionResponse,
    GetTransactionResponse,
    UpdateStatusResponse
)
from aegis_shared.generated.transaction_pb2 import RiskFactor as RiskFactorProto

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
        """Maps internal transaction data to CreateTransactionResponse proto."""
        
        # 1. Standardize data access (Pydantic vs Dict vs ORM)
        if hasattr(internal_obj, "model_dump"):
            data = internal_obj.model_dump()
        elif hasattr(internal_obj, "__dict__"):
            data = internal_obj.__dict__
        else:
            data = internal_obj

        # 2. Map nested risk factors into actual Protobuf instances
        raw_factors = data.get("risk_factors") or []
        proto_factors = []
        for rf in raw_factors:
            # Handle if rf is a Pydantic model or a dictionary
            f_name = rf.get("factor") if isinstance(rf, dict) else getattr(rf, "factor", "")
            f_sev = rf.get("severity") if isinstance(rf, dict) else getattr(rf, "severity", "")
            f_det = rf.get("detail") if isinstance(rf, dict) else getattr(rf, "detail", "")
            
            proto_factors.append(RiskFactorProto(
                factor=f_name,
                severity=cls._format_field(f_sev),
                detail=f_det
            ))

        return CreateTransactionResponse(
            transaction_id=cls._format_field(data.get("transaction_id")),
            idempotency_key=data.get("idempotency_key", ""),
            amount=cls._format_field(data.get("amount")),
            currency=data.get("currency", ""),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            status=cls._format_field(data.get("status")),
            created_at=cls._format_field(data.get("created_at")),
            already_existed=bool(data.get("already_existed", False)),
            sender_country=data.get("sender_country", ""),
            receiver_country=data.get("receiver_country", ""),
            decision=cls._format_field(data.get("decision")),
            risk_score=float(data.get("risk_score", 0.0)),
            risk_factors=proto_factors,
            risk_level=cls._format_field(data.get("risk_level")),
        )

    @classmethod
    def to_get_proto(cls, internal_obj) -> GetTransactionResponse:
        """Maps internal transaction data to GetTransactionResponse proto."""
        if hasattr(internal_obj, "model_dump"):
            data = internal_obj.model_dump()
        elif hasattr(internal_obj, "__dict__"):
            data = internal_obj.__dict__
        else:
            data = internal_obj
        
        return GetTransactionResponse(
            transaction_id=cls._format_field(data.get("transaction_id")),
            idempotency_key=data.get("idempotency_key", ""),
            amount=cls._format_field(data.get("amount")),
            currency=data.get("currency", ""),
            sender_id=data.get("sender_id", ""),
            receiver_id=data.get("receiver_id", ""),
            sender_country=data.get("sender_country", ""),
            receiver_country=data.get("receiver_country", ""),
            status=cls._format_field(data.get("status")),
            created_at=cls._format_field(data.get("created_at")),
            updated_at=cls._format_field(data.get("updated_at"))
        )

    @staticmethod
    def to_update_status_proto(result_dict: dict) -> UpdateStatusResponse:
        """Maps repository result dict to UpdateStatusResponse proto."""
        return UpdateStatusResponse(
            transaction_id=str(result_dict.get("transaction_id", "")),
            previous_status=str(result_dict.get("previous_status", "")),
            new_status=str(result_dict.get("new_status", "")),
            success=bool(result_dict.get("success", False))
        )