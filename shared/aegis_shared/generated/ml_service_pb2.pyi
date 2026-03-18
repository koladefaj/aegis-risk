from aegis_shared.generated import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ScoreTransactionRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id", "amount", "currency", "sender_id", "receiver_id", "sender_country", "receiver_country", "device_fingerprint", "channel", "created_at")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    amount: float
    currency: str
    sender_id: str
    receiver_id: str
    sender_country: str
    receiver_country: str
    device_fingerprint: str
    channel: str
    created_at: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., sender_id: _Optional[str] = ..., receiver_id: _Optional[str] = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ..., device_fingerprint: _Optional[str] = ..., channel: _Optional[str] = ..., created_at: _Optional[str] = ...) -> None: ...

class ScoreTransactionResponse(_message.Message):
    __slots__ = ("transaction_id", "anomaly_score", "model_version", "fallback_used", "feature_contributions")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    ANOMALY_SCORE_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    FALLBACK_USED_FIELD_NUMBER: _ClassVar[int]
    FEATURE_CONTRIBUTIONS_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    anomaly_score: float
    model_version: str
    fallback_used: bool
    feature_contributions: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, transaction_id: _Optional[str] = ..., anomaly_score: _Optional[float] = ..., model_version: _Optional[str] = ..., fallback_used: bool = ..., feature_contributions: _Optional[_Iterable[str]] = ...) -> None: ...
