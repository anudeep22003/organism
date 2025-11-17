from dataclasses import dataclass, field
from typing import Generic, TypeVar

from core.common.utils import get_current_timestamp_seconds

T = TypeVar("T")


@dataclass(frozen=True)
class BaseEvent(Generic[T]):
    target_room: str
    data: T
    created_at: int = field(default_factory=get_current_timestamp_seconds)
