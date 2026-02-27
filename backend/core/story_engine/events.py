import uuid
from enum import Enum
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_ms


class EventType(Enum):
    STREAM_START = "stream.start"
    STREAM_CHUNK = "stream.chunk"
    STREAM_END = "stream.end"
    STREAM_ERROR = "stream.error"


class ErrorPayload(AliasedBaseModel):
    code: str
    message: str
    retryable: bool = False
    details: dict[str, Any] | None = None


class EventEnvelope(AliasedBaseModel):
    schema_version: int = 1
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts_ms: int = Field(default_factory=get_current_timestamp_ms)

    request_id: str | None = None
    stream_id: str | None = None
    seq: int | None = None
    event_type: EventType

    payload: dict[str, Any] | None = None
    error: ErrorPayload | None = None
