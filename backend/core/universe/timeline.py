import asyncio
from ast import TypeVar
from collections import defaultdict
from typing import Any, Awaitable, Callable, Type

from loguru import logger

from agents.types import DirectorRequest
from core.singleton import SingletonMeta
from core.universe.events import BaseEvent

logger = logger.bind(name=__name__)

# TODO maybe add bound as BaseEvent?
T = TypeVar("T")


class SubscriptionKey:
    """Composite key for routing: (event_type, sid)"""

    def __init__(self, event_type: Type[Any], sid: str | None) -> None:
        self.event_type = event_type
        self.sid = sid

    def __hash__(self) -> int:
        return hash((self.event_type, self.sid))

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SubscriptionKey):
            return False
        return self.event_type == other.event_type and self.sid == other.sid

    def matches(self, event: BaseEvent) -> bool:
        """Check if this subscription key matches the given event"""
        if not isinstance(event.data, self.event_type):
            return False
        # Check if sid matches (None means match all)
        if self.sid is None or self.sid == event.sid:
            return True
        return False


class Timeline(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.events: asyncio.Queue[Any] = asyncio.Queue()
        self.subscribers: defaultdict[
            SubscriptionKey, list[Callable[[BaseEvent], Awaitable[None]]]
        ] = defaultdict(list)

    def subscribe(
        self, event_data_type: Type[T], handler: Callable[[BaseEvent], Awaitable[None]], sid: str | None = None
    ) -> SubscriptionKey:
        subscription_key = SubscriptionKey(event_data_type, sid)
        logger.info(f"Timeline: subscribing to event: {event_data_type.__name__} for sid: {sid} with handler: {handler}")
        self.subscribers[subscription_key].append(handler)
        return subscription_key # return this so can unsubscribe later

    def unsubscribe(
        self,
        subscription_key: SubscriptionKey,
        handler: Callable[[BaseEvent], Awaitable[None]] | None = None,
    ) -> None:
        if handler is None:
            # Remove all handlers for this key
            self.subscribers.pop(subscription_key)
        else:
            if subscription_key in self.subscribers and handler in self.subscribers[subscription_key]:
                self.subscribers[subscription_key].remove(handler)

    async def add_event(self, event: BaseEvent[Any]) -> None:
        """Add event and route to matching handlers"""
        logger.info(f"Timeline: adding event: {event.data.__class__.__name__} for sid: {event.sid}")
        await self.events.put(event)
        for subscription_key, handlers in self.subscribers.items():
            if subscription_key.matches(event):
                for handler in handlers:
                    await handler(event)

    async def get_events(self) -> list[Any]:
        events = []
        while not self.events.empty():
            events.append(await self.events.get())
        return events


primary_timeline = Timeline()
