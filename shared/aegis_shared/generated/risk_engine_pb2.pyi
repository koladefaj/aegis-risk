from aegis_shared.generated import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class StreamExplanationRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ...) -> None: ...

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

class EvaluateRiskRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id", "amount", "currency", "sender_id", "receiver_id", "sender_country", "receiver_country", "device_fingerprint", "ip_address", "channel", "created_at")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    AMOUNT_FIELD_NUMBER: _ClassVar[int]
    CURRENCY_FIELD_NUMBER: _ClassVar[int]
    SENDER_ID_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_ID_FIELD_NUMBER: _ClassVar[int]
    SENDER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    RECEIVER_COUNTRY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_FINGERPRINT_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
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
    ip_address: str
    channel: str
    created_at: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ..., amount: _Optional[float] = ..., currency: _Optional[str] = ..., sender_id: _Optional[str] = ..., receiver_id: _Optional[str] = ..., sender_country: _Optional[str] = ..., receiver_country: _Optional[str] = ..., device_fingerprint: _Optional[str] = ..., ip_address: _Optional[str] = ..., channel: _Optional[str] = ..., created_at: _Optional[str] = ...) -> None: ...

class RiskFactor(_message.Message):
    __slots__ = ("factor", "severity", "detail")
    FACTOR_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    DETAIL_FIELD_NUMBER: _ClassVar[int]
    factor: str
    severity: str
    detail: str
    def __init__(self, factor: _Optional[str] = ..., severity: _Optional[str] = ..., detail: _Optional[str] = ...) -> None: ...

class RuleFlagResult(_message.Message):
    __slots__ = ("rule_name", "triggered", "score", "reason")
    RULE_NAME_FIELD_NUMBER: _ClassVar[int]
    TRIGGERED_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    rule_name: str
    triggered: bool
    score: float
    reason: str
    def __init__(self, rule_name: _Optional[str] = ..., triggered: bool = ..., score: _Optional[float] = ..., reason: _Optional[str] = ...) -> None: ...

class EvaluateRiskResponse(_message.Message):
    __slots__ = ("transaction_id", "decision", "risk_score", "risk_level", "confidence", "risk_factors", "processing_time_ms", "model_version")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    RISK_FACTORS_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    decision: str
    risk_score: float
    risk_level: str
    confidence: str
    risk_factors: _containers.RepeatedCompositeFieldContainer[RiskFactor]
    processing_time_ms: float
    model_version: str
    def __init__(self, transaction_id: _Optional[str] = ..., decision: _Optional[str] = ..., risk_score: _Optional[float] = ..., risk_level: _Optional[str] = ..., confidence: _Optional[str] = ..., risk_factors: _Optional[_Iterable[_Union[RiskFactor, _Mapping]]] = ..., processing_time_ms: _Optional[float] = ..., model_version: _Optional[str] = ...) -> None: ...

class GetRiskResultResponse(_message.Message):
    __slots__ = ("transaction_id", "decision", "risk_score", "risk_level", "risk_factors", "rule_flags", "ml_anomaly_score", "ml_fallback_used", "ml_model_version", "llm_summary", "llm_risk_factors", "llm_recommendation", "llm_fallback_used", "processing_time_ms", "worker_id", "evaluated_at")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    DECISION_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    RISK_FACTORS_FIELD_NUMBER: _ClassVar[int]
    RULE_FLAGS_FIELD_NUMBER: _ClassVar[int]
    ML_ANOMALY_SCORE_FIELD_NUMBER: _ClassVar[int]
    ML_FALLBACK_USED_FIELD_NUMBER: _ClassVar[int]
    ML_MODEL_VERSION_FIELD_NUMBER: _ClassVar[int]
    LLM_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    LLM_RISK_FACTORS_FIELD_NUMBER: _ClassVar[int]
    LLM_RECOMMENDATION_FIELD_NUMBER: _ClassVar[int]
    LLM_FALLBACK_USED_FIELD_NUMBER: _ClassVar[int]
    PROCESSING_TIME_MS_FIELD_NUMBER: _ClassVar[int]
    WORKER_ID_FIELD_NUMBER: _ClassVar[int]
    EVALUATED_AT_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    decision: str
    risk_score: float
    risk_level: str
    risk_factors: _containers.RepeatedCompositeFieldContainer[RiskFactor]
    rule_flags: _containers.RepeatedCompositeFieldContainer[RuleFlagResult]
    ml_anomaly_score: float
    ml_fallback_used: bool
    ml_model_version: str
    llm_summary: str
    llm_risk_factors: _containers.RepeatedScalarFieldContainer[str]
    llm_recommendation: str
    llm_fallback_used: bool
    processing_time_ms: float
    worker_id: str
    evaluated_at: str
    def __init__(self, transaction_id: _Optional[str] = ..., decision: _Optional[str] = ..., risk_score: _Optional[float] = ..., risk_level: _Optional[str] = ..., risk_factors: _Optional[_Iterable[_Union[RiskFactor, _Mapping]]] = ..., rule_flags: _Optional[_Iterable[_Union[RuleFlagResult, _Mapping]]] = ..., ml_anomaly_score: _Optional[float] = ..., ml_fallback_used: bool = ..., ml_model_version: _Optional[str] = ..., llm_summary: _Optional[str] = ..., llm_risk_factors: _Optional[_Iterable[str]] = ..., llm_recommendation: _Optional[str] = ..., llm_fallback_used: bool = ..., processing_time_ms: _Optional[float] = ..., worker_id: _Optional[str] = ..., evaluated_at: _Optional[str] = ...) -> None: ...

class GetRiskResultRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ...) -> None: ...
