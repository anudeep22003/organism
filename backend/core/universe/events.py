
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Generic, TYPE_CHECKING, TypeVar

from pydantic import Field

from core.sockets.types.envelope import AliasedBaseModel

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

def get_current_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)

T = TypeVar("T")

@dataclass(frozen=True)
class BaseEvent(Generic[T]):
    sid: str 
    sio: "AsyncServer" 
    data: T
    created_at: int = field(default_factory=get_current_timestamp)
