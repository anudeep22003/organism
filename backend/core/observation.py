from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Observation:
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    user_prompt: str | None = None
    story: str | None = None
