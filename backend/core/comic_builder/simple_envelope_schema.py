import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_seconds


class SimpleEnvelope(AliasedBaseModel):
    """Envelope for streaming responses."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(default_factory=get_current_timestamp_seconds)

    request_id: str | None = None
    stream_id: str | None = None
    seq: int | None = None

    data: dict[str, Any]
