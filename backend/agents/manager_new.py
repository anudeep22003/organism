from typing import TYPE_CHECKING

from loguru import logger

from agents.types import DirectorRequest
from core.universe.events import BaseEvent

if TYPE_CHECKING:
    from socketio import AsyncServer

logger = logger.bind(name=__name__)


class ManagerNew:
    def __init__(self, target_room: str, sio: "AsyncServer") -> None:
        self.target_room = target_room
        self.sio = sio
        self.context = {}

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        logger.debug("Event Received", **event.data.model_dump())
        return None
