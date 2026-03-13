from aegis_shared.generated import common_pb2 as _common_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateTransactionRequest(_message.Message):
    __slots__ = ("metadata", "idempotency_key", "amount", "currency", "sender_id", "receiver_id", "sender_country", "receiver_country", "device_fingerprint", "ip_address", "channel")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    idempotency_key: str
    amount: str
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    device_fingerprint: str
    ip_address: str
    channel: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., idempotency_key: _Optional[str] = ..., amount: _Optional[str] = ..., currency: _Optional[str] = ..., sender_id: _Optional[str] = ..., receiver_id: _Optional[str] = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ..., device_fingerprint: _Optional[str] = ..., ip_address: _Optional[str] = ..., channel: _Optional[str] = ...) -> None: ...

class CreateTransactionResponse(_message.Message):
    __slots__ = ("transaction_id", "idempotency_key", "amount", "currency", "sender_id", "receiver_id", "status", "created_at", "already_existed", "sender_country", "receiver_country")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    ALREADY_EXISTED_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    idempotency_key: str
    amount: str
    currency: str
    sender_id: str
    receiver_id: str
    status: str
    created_at: str
    already_existed: bool
    sender_country: str
    receiver_country: str
    def __init__(self, transaction_id: _Optional[str] = ..., idempotency_key: _Optional[str] = ..., amount: _Optional[str] = ..., currency: _Optional[str] = ..., sender_id: _Optional[str] = ..., receiver_id: _Optional[str] = ..., status: _Optional[str] = ..., created_at: _Optional[str] = ..., already_existed: bool = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ...) -> None: ...

class GetTransactionRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ...) -> None: ...

class GetTransactionResponse(_message.Message):
    __slots__ = ("transaction_id", "idempotency_key", "amount", "currency", "sender_id", "receiver_id", "sender_country", "receiver_country", "status", "created_at", "updated_at")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    IDEMPOTENCY_KEY_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    UPDATED_AT_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    idempotency_key: str
    amount: str
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    status: str
    created_at: str
    updated_at: str
    def __init__(self, transaction_id: _Optional[str] = ..., idempotency_key: _Optional[str] = ..., amount: _Optional[str] = ..., currency: _Optional[str] = ..., sender_id: _Optional[str] = ..., receiver_id: _Optional[str] = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ..., status: _Optional[str] = ..., created_at: _Optional[str] = ..., updated_at: _Optional[str] = ...) -> None: ...

class UpdateStatusRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id", "new_status", "reason")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    new_status: str
    reason: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ..., new_status: _Optional[str] = ..., reason: _Optional[str] = ...) -> None: ...

class UpdateStatusResponse(_message.Message):
    __slots__ = ("transaction_id", "previous_status", "new_status", "success")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    PREVIOUS_STATUS_FIELD_NUMBER: _ClassVar[int]
    NEW_STATUS_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    previous_status: str
    new_status: str
    success: bool
    def __init__(self, transaction_id: _Optional[str] = ..., previous_status: _Optional[str] = ..., new_status: _Optional[str] = ..., success: bool = ...) -> None: ...
