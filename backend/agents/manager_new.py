import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Literal

from loguru import logger

from agents.types import DirectorRequest
from core.common import AliasedBaseModel
from core.sockets.types.envelope import Actor
from core.sockets.utils.emit_helpers import emit_text_start_chunk_end_events
from core.universe.events import BaseEvent

if TYPE_CHECKING:
    from socketio import AsyncServer

logger = logger.bind(name=__name__)

plan: dict = {1: "story-writer"}


class StoryRequestEvent(AliasedBaseModel):
    prompt: str


@dataclass
class Stage:
    order: int
    task: str
    handle_function: Callable[[], None]
    status: Literal["pending", "in_progress", "completed", "failed"]
    notify_function: Callable[[str | None], None]
    output: dict | None = None


class StoryWriter:
    def __init__(self) -> None:
        pass

    async def handle(self, stage: Stage) -> None:
        logger.debug("I the story writer received the story request event")
        stage.status = "in_progress"
        stage.output = {}
        await stage.notify_function("I have started the story writer")
        stage.status = "completed"
        await stage.notify_function("I have completed the story writer")


class ManagerNew:
    def __init__(self, target_room: str, sio: "AsyncServer") -> None:
        self.target_room = target_room
        self.sio = sio
        self.request_id = str(uuid.uuid4())
        self.plan: list[Stage] = self.build_plan()

    def build_plan(self) -> None:
        return [
            Stage(
                order=1,
                task="story-writer",
                handle_function=StoryWriter().handle,
                notify_function=self.notify_user,
                status="pending",
                output=None,
            ),
        ]

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        logger.debug("Event Received", **event.data.model_dump())
        await self.notify_user()
        for stage in self.plan:
            if stage.status == "pending":
                await stage.handle_function(stage)
                break
        return None

    async def notify_user(self, message: str | None = None) -> None:
        stream_id = str(uuid.uuid4())
        if message is None:
            message = "I have received your task, just thought you should know."
        notification_string = message
        actor: Actor = "tasknotifier"
        await emit_text_start_chunk_end_events(
            sio=self.sio,
            target_room=self.target_room,
            actor=actor,
            request_id=self.request_id,
            stream_id=stream_id,
            text=notification_string,
        )
