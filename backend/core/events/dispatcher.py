import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable

from .models import Event, EventStatus, EventType
from .repository import EventRepository


class EventNotFoundError(Exception):
    """Event not found."""

    pass


@dataclass(frozen=True, slots=True)
class UpdateEventParams:
    event_id: uuid.UUID
    status: EventStatus
    processed_at: datetime
    claimed_at: datetime
    failed_at: datetime | None
    last_error: str | None


@dataclass(frozen=True, slots=True)
class DispatchEventForHandling:
    event_id: uuid.UUID
    event_retreiver_fn: Callable[
        [uuid.UUID], Awaitable[Event]
    ]  # to get the event from the db
    confirm_handling_fn: (
        Callable[
            [uuid.UUID, UpdateEventParams], Awaitable[None]
        ]  # to succeed, fail, or error after attempting to handle
    )


DispatchHandlerMap = dict[
    EventType, list[Callable[[DispatchEventForHandling], Awaitable[None]]]
]


class EventDispatcher:
    def __init__(
        self,
        repository: "EventRepository",
        dispatch_handlers_map: DispatchHandlerMap,
    ) -> None:
        self.repository = repository
        self.dispatch_handlers_map = dispatch_handlers_map

    async def dispatch_event_for_handling(
        self, event_id: uuid.UUID, event_type: EventType
    ) -> None:
        dispatch_event_for_handling = DispatchEventForHandling(
            event_id=event_id,
            event_retreiver_fn=self._retreive_event_for_handling,
            confirm_handling_fn=self._confirm_handling_fn,
        )
        handlers = self.dispatch_handlers_map[event_type]
        for handler in handlers:
            await handler(dispatch_event_for_handling)

    async def _retreive_event_for_handling(self, event_id: uuid.UUID) -> Event:
        event = await self.repository.get_event_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")
        return event

    async def _confirm_handling_fn(
        self, event_id: uuid.UUID, params: UpdateEventParams
    ) -> None:
        event = await self.repository.get_event_by_id(event_id)
        if event is None:
            raise EventNotFoundError(f"Event {event_id} not found")
        await self.repository.update_event(
            event,
            status=params.status,
            claimed_at=params.claimed_at,
            processed_at=params.processed_at,
            failed_at=params.failed_at,
            last_error=params.last_error,
        )
