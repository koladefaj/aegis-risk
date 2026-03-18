from aegis_shared.generated import common_pb2 as _common_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class RegisterWebhookRequest(_message.Message):
    __slots__ = ("metadata", "client_id", "url", "events")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    client_id: str
    url: str
    events: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., client_id: _Optional[str] = ..., url: _Optional[str] = ..., events: _Optional[_Iterable[str]] = ...) -> None: ...

class RegisterWebhookResponse(_message.Message):
    __slots__ = ("webhook_id", "url", "client_id", "events", "created_at")
    WEBHOOK_ID_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    EVENTS_FIELD_NUMBER: _ClassVar[int]
    CREATED_AT_FIELD_NUMBER: _ClassVar[int]
    webhook_id: str
    url: str
    client_id: str
    events: _containers.RepeatedScalarFieldContainer[str]
    created_at: str
    def __init__(self, webhook_id: _Optional[str] = ..., url: _Optional[str] = ..., client_id: _Optional[str] = ..., events: _Optional[_Iterable[str]] = ..., created_at: _Optional[str] = ...) -> None: ...

class SendNotificationRequest(_message.Message):
    __slots__ = ("metadata", "transaction_id", "event", "risk_score", "risk_level", "triggered_rules", "explanation_summary", "evaluated_at")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_FIELD_NUMBER: _ClassVar[int]
    RISK_SCORE_FIELD_NUMBER: _ClassVar[int]
    RISK_LEVEL_FIELD_NUMBER: _ClassVar[int]
    TRIGGERED_RULES_FIELD_NUMBER: _ClassVar[int]
    EXPLANATION_SUMMARY_FIELD_NUMBER: _ClassVar[int]
    EVALUATED_AT_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    transaction_id: str
    event: str
    risk_score: float
    risk_level: str
    triggered_rules: _containers.RepeatedScalarFieldContainer[str]
    explanation_summary: str
    evaluated_at: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., transaction_id: _Optional[str] = ..., event: _Optional[str] = ..., risk_score: _Optional[float] = ..., risk_level: _Optional[str] = ..., triggered_rules: _Optional[_Iterable[str]] = ..., explanation_summary: _Optional[str] = ..., evaluated_at: _Optional[str] = ...) -> None: ...

class SendNotificationResponse(_message.Message):
    __slots__ = ("transaction_id", "webhooks_triggered", "success")
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    WEBHOOKS_TRIGGERED_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    transaction_id: str
    webhooks_triggered: int
    success: bool
    def __init__(self, transaction_id: _Optional[str] = ..., webhooks_triggered: _Optional[int] = ..., success: bool = ...) -> None: ...

class GetWebhookStatusRequest(_message.Message):
    __slots__ = ("metadata", "webhook_id")
    METADATA_FIELD_NUMBER: _ClassVar[int]
    WEBHOOK_ID_FIELD_NUMBER: _ClassVar[int]
    metadata: _common_pb2.RequestMetadata
    webhook_id: str
    def __init__(self, metadata: _Optional[_Union[_common_pb2.RequestMetadata, _Mapping]] = ..., webhook_id: _Optional[str] = ...) -> None: ...

class GetWebhookStatusResponse(_message.Message):
    __slots__ = ("webhook_id", "url", "status", "delivery_count", "failure_count")
    WEBHOOK_ID_FIELD_NUMBER: _ClassVar[int]
    URL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    DELIVERY_COUNT_FIELD_NUMBER: _ClassVar[int]
    FAILURE_COUNT_FIELD_NUMBER: _ClassVar[int]
    webhook_id: str
    url: str
    status: str
    delivery_count: int
    failure_count: int
    def __init__(self, webhook_id: _Optional[str] = ..., url: _Optional[str] = ..., status: _Optional[str] = ..., delivery_count: _Optional[int] = ..., failure_count: _Optional[int] = ...) -> None: ...
