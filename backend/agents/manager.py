from loguru import logger
from core.sockets.types.envelope import Actor
from core.universe.events import BaseEvent

logger = logger.bind(name=__name__)


class Manager:
    actor_name: Actor = "manager"

    @staticmethod
    async def handle_event(event: BaseEvent) -> None:
        logger.info(f"Manager received event", event=event)