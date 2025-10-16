
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import Field

from core.sockets.types.envelope import AliasedBaseModel

def get_current_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)

T = TypeVar("T")

class BaseEvent(AliasedBaseModel, Generic[T]):
    sid: str = Field(description="Who this event came from")
    created_at: int = Field(default_factory=get_current_timestamp)
    data: T
