import uuid
from dataclasses import dataclass
from typing import Literal

from loguru import logger


@dataclass(frozen=True, slots=True)
class AuthLogEvent:
    event: str
    route: str | None = None
    user_id: uuid.UUID | None = None
    google_sub: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    reason: str | None = None
    retry_after: int | None = None

    def to_log_extra(self) -> dict[str, str | int]:
        extra: dict[str, str | int] = {"event": self.event}
        if self.route is not None:
            extra["route"] = self.route
        if self.user_id is not None:
            extra["user_id"] = str(self.user_id)
        if self.google_sub is not None:
            extra["google_sub"] = self.google_sub
        if self.ip is not None:
            extra["ip"] = self.ip
        if self.user_agent is not None:
            extra["user_agent"] = self.user_agent
        if self.reason is not None:
            extra["reason"] = self.reason
        if self.retry_after is not None:
            extra["retry_after"] = self.retry_after
        return extra


def log_auth_event(
    event: str,
    *,
    level: Literal["info", "warning", "error"] = "info",
    route: str | None = None,
    user_id: uuid.UUID | None = None,
    google_sub: str | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    reason: str | None = None,
    retry_after: int | None = None,
) -> None:
    auth_log_event = AuthLogEvent(
        event=event,
        route=route,
        user_id=user_id,
        google_sub=google_sub,
        ip=ip,
        user_agent=user_agent,
        reason=reason,
        retry_after=retry_after,
    )

    logger.bind(**auth_log_event.to_log_extra()).log(level.upper(), event)
