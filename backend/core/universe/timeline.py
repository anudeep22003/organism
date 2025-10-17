import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable, Type
from agents.types import DirectorRequest
from core.singleton import SingletonMeta
from core.universe.events import BaseEvent

from loguru import logger

logger = logger.bind(name=__name__)

class Timeline(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.events: asyncio.Queue[Any] = asyncio.Queue()
        self.subscribers: defaultdict[Type[Any], list[Callable[[BaseEvent], Awaitable[None]]]] = defaultdict(list)
    
    def subscribe(self, event: Type[Any], handler: Callable[[BaseEvent], Awaitable[None]]) -> None:
        logger.info(f"Timeline: subscribing to event: {event} with handler: {handler}")
        self.subscribers[event].append(handler)

    def unsubscribe(self, handler: Callable[[BaseEvent], Awaitable[None]], event: Type[Any] | None = None) -> None:
        if event is None:
            for _, handlers in self.subscribers.items():
                if handler in handlers:
                    handlers.remove(handler)
        else:
            if handler in self.subscribers[event]:
                self.subscribers[event].remove(handler)

    async def add_event(self, event: Any) -> None:
        logger.info(f"Timeline: adding event: {event}")
        await self.events.put(event)
        logger.info(f"Timeline: subscribers: {self.subscribers}")
        logger.info(f"Timeline: event type: {type(event)}")
        # handlers_subscribed_to_event = self.subscribers[type(event)]
        handlers_subscribed_to_event = self.subscribers[BaseEvent[DirectorRequest]]
        logger.info(f"Timeline: handlers subscribed to event: {handlers_subscribed_to_event}")
        for handler in handlers_subscribed_to_event:
            logger.info(f"Timeline: calling handler: {handler}")
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Timeline: error calling handler: {e}")
                raise e

    async def get_events(self) -> list[Any]:
        events = []
        while not self.events.empty():
            events.append(await self.events.get())
        return events

primary_timeline = Timeline()