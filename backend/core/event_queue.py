import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Awaitable, Callable, Type

from core.observation import Observation
from core.singleton import SingletonMeta

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ObservationUpdatedEvent:
    sid: str
    observation: Observation
    sio: "AsyncServer"


class EventBus(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.event_queue: asyncio.Queue[ObservationUpdatedEvent] = asyncio.Queue()
        self.subscribers: list[
            tuple[
                Type[ObservationUpdatedEvent],
                Callable[[ObservationUpdatedEvent], Awaitable[None]],
            ]
        ] = []

    async def publish(self, event: ObservationUpdatedEvent):
        await self.event_queue.put(event)
        for event_type, subscriber in self.subscribers:
            if isinstance(event, event_type):
                await subscriber(event)

    def add_subscriber(
        self,
        event_type: Type[ObservationUpdatedEvent],
        subscriber_handler: Callable[[ObservationUpdatedEvent], Awaitable[None]],
    ):
        self.subscribers.append((event_type, subscriber_handler))


def initialize_event_subscribers() -> None:
    from agents.scriptwriter import scriptwriter

    event_bus = EventBus()

    event_bus.add_subscriber(
        ObservationUpdatedEvent, scriptwriter.handle_observation_updated
    )
