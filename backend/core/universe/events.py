from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Generic, TypeVar


def get_current_timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


T = TypeVar("T")


@dataclass(frozen=True)
class BaseEvent(Generic[T]):
    target_room: str
    data: T
    created_at: int = field(default_factory=get_current_timestamp)
