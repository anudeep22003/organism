import uuid
from typing import TYPE_CHECKING

from loguru import logger

from agents.types import DirectorRequest
from core.sockets.types.envelope import Actor
from core.sockets.utils.emit_helpers import emit_text_start_chunk_end_events
from core.universe.events import BaseEvent

if TYPE_CHECKING:
    from socketio import AsyncServer

logger = logger.bind(name=__name__)

plan: dict = {1: "story-writer"}


class StoryWriter:
    def __init__(self) -> None:
        pass

    def execute(self) -> None:
        pass


class ManagerNew:
    def __init__(self, target_room: str, sio: "AsyncServer") -> None:
        self.target_room = target_room
        self.sio = sio
        self.request_id = str(uuid.uuid4())

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        logger.debug("Event Received", **event.data.model_dump())
        await self.notify_user()
        return None

    async def notify_user(self) -> None:
        stream_id = str(uuid.uuid4())
        notification_string = "I have received your task, just thought you should know."
        actor: Actor = "tasknotifier"
        await emit_text_start_chunk_end_events(
            sio=self.sio,
            target_room=self.target_room,
            actor=actor,
            request_id=self.request_id,
            stream_id=stream_id,
            text=notification_string,
        )
