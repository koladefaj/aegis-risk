"""Unit tests for TransactionMapper."""

import pytest
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4

from app.mappers.transaction_mapper import TransactionMapper


class TestFormatField:
    """Tests for the _format_field helper."""

    def test_none_returns_empty_string(self):
        assert TransactionMapper._format_field(None) == ""

    def test_uuid_returns_string(self):
        uid = uuid4()
        assert TransactionMapper._format_field(uid) == str(uid)

    def test_decimal_returns_string(self):
        d = Decimal("123.45")
        assert TransactionMapper._format_field(d) == "123.45"

    def test_datetime_returns_isoformat(self):
        dt = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)
        result = TransactionMapper._format_field(dt)
        assert "2026-01-15" in result

    def test_plain_string_passthrough(self):
        assert TransactionMapper._format_field("hello") == "hello"

    def test_enum_with_value_attribute(self):
        from aegis_shared.enums import TransactionStatus
        assert TransactionMapper._format_field(TransactionStatus.RECEIVED) == "RECEIVED"


class TestToCreateProto:
    """Tests for to_create_proto mapping."""

    def test_maps_all_fields(self):
        txn_id = uuid4()
        now = datetime.now(UTC)

        data = {
            "transaction_id": txn_id,
            "idempotency_key": "key-1234567890",
            "amount": Decimal("100.50"),
            "currency": "USD",
            "sender_id": "s1",
            "receiver_id": "r1",
            "status": "RECEIVED",
            "created_at": now,
            "already_existed": False,
            "sender_country": "US",
            "receiver_country": "GB",
        }

        # Use a SimpleNamespace-like object with __dict__
        class MockObj:
            def get(self, key, default=None):
                return data.get(key, default)

            def __getattr__(self, name):
                return data.get(name)

        obj = MockObj()
        obj.__dict__ = data

        result = TransactionMapper.to_create_proto(obj)

        assert result.transaction_id == str(txn_id)
        assert result.idempotency_key == "key-1234567890"
        assert result.amount == "100.50"
        assert result.currency == "USD"
        assert result.sender_id == "s1"
        assert result.receiver_id == "r1"
        assert result.status == "RECEIVED"
        assert result.already_existed is False
        assert result.sender_country == "US"
        assert result.receiver_country == "GB"


class TestToGetProto:
    """Tests for to_get_proto mapping."""

    def test_maps_all_fields_including_updated_at(self):
        txn_id = uuid4()
        now = datetime.now(UTC)

        data = {
            "transaction_id": txn_id,
            "idempotency_key": "key-0987654321",
            "amount": Decimal("200.00"),
            "currency": "EUR",
            "sender_id": "s2",
            "receiver_id": "r2",
            "sender_country": "DE",
            "receiver_country": "FR",
            "status": "COMPLETED",
            "created_at": now,
            "updated_at": now,
        }

        class MockObj:
            def get(self, key, default=None):
                return data.get(key, default)

        obj = MockObj()
        obj.__dict__ = data

        result = TransactionMapper.to_get_proto(obj)

        assert result.transaction_id == str(txn_id)
        assert result.currency == "EUR"
        assert result.updated_at != ""


class TestToUpdateStatusProto:
    """Tests for to_update_status_proto mapping."""

    def test_maps_dict_correctly(self):
        txn_id = uuid4()

        result_dict = {
            "transaction_id": txn_id,
            "previous_status": "RECEIVED",
            "new_status": "PROCESSING",
            "success": True,
        }

        result = TransactionMapper.to_update_status_proto(result_dict)

        assert result.transaction_id == str(txn_id)
        assert result.previous_status == "RECEIVED"
        assert result.new_status == "PROCESSING"
        assert result.success is True

    def test_failed_transition(self):
        result_dict = {
            "transaction_id": uuid4(),
            "previous_status": "PROCESSING",
            "new_status": "FAILED",
            "success": True,
        }

        result = TransactionMapper.to_update_status_proto(result_dict)

        assert result.new_status == "FAILED"
        assert result.success is True
