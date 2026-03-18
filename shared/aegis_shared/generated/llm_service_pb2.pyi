from aegis_shared.generated import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExplainRiskRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id", "risk_score", "risk_level", "triggered_rules", "ml_anomaly_score", "amount", "currency", "sender_country", "receiver_country")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    TRIGGERED_RULES_FIELD_NUMBER: _ClassVar[int]
    ML_ANOMALY_SCORE_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    risk_score: float
    risk_level: str
    triggered_rules: _containers.RepeatedScalarFieldContainer[str]
    ml_anomaly_score: float
    amount: float
    currency: str
    sender_country: str
    receiver_country: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ..., risk_score: _Optional[float] = ..., risk_level: _Optional[str] = ..., triggered_rules: _Optional[_Iterable[str]] = ..., ml_anomaly_score: _Optional[float] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ...) -> None: ...

class ExplainRiskResponse(_message.Message):
    __slots__ = ("transaction_id", "summary", "risk_factors", "recommendation", "confidence", "fallback_used")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    SUMMARY_FIELD_NUMBER: _ClassVar[int]
    RISK_FACTORS_FIELD_NUMBER: _ClassVar[int]
    RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    FALLBACK_USED_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    summary: str
    risk_factors: _containers.RepeatedScalarFieldContainer[str]
    recommendation: str
    confidence: float
    fallback_used: bool
    def __init__(self, transaction_id: _Optional[str] = ..., summary: _Optional[str] = ..., risk_factors: _Optional[_Iterable[str]] = ..., recommendation: _Optional[str] = ..., confidence: _Optional[float] = ..., fallback_used: bool = ...) -> None: ...

class ExplanationChunk(_message.Message):
    __slots__ = ("transaction_id", "chunk_type", "content", "index")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    CHUNK_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    chunk_type: str
    content: str
    index: int
    def __init__(self, transaction_id: _Optional[str] = ..., chunk_type: _Optional[str] = ..., content: _Optional[str] = ..., index: _Optional[int] = ...) -> None: ...
