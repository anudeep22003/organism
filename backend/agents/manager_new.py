import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

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


class Notifier(Protocol):
    """Unified interface for sending messages to the user."""

    async def send(self, message: str, actor: Actor = "tasknotifier") -> None:
        """Send a simple message"""
        ...


@dataclass(frozen=True)
class CommunicationDetails:
    request_id: str
    sio: "AsyncServer"
    target_room: str


@dataclass
class SocketNotifier:
    """Concrete implementation of the notifier interface for socketio."""

    communication_details: CommunicationDetails

    async def send(self, message: str, actor: Actor = "tasknotifier") -> None:
        """Send a simple message"""
        stream_id = str(uuid.uuid4())
        await emit_text_start_chunk_end_events(
            sio=self.communication_details.sio,
            target_room=self.communication_details.target_room,
            request_id=self.communication_details.request_id,
            actor=actor,
            stream_id=stream_id,
            text=f"Notification: {message}",
        )


class StoryRequestEvent(AliasedBaseModel):
    prompt: str


@dataclass
class Stage:
    """Pure data describing work to be done."""

    task: str
    agent_type: str


class StageStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageResult:
    """What an agent produces after handling a stage."""

    status: StageStatus
    output: Any = None
    error: str | None = None


@dataclass
class ExecutionContext:
    """Everything an Agent needs to do its work."""

    task: str
    communication_details: CommunicationDetails
    notifier: Notifier
    _status: StageStatus = StageStatus.PENDING
    previous_results: dict[str, StageResult] = field(default_factory=dict)

    @property
    def status(self) -> StageStatus:
        return self._status

    @status.setter
    def status(self, value: StageStatus) -> None:
        self._status = value

    async def update_status(self, new_status: StageStatus) -> None:
        self.status = new_status
        await self.notifier.send(f"The status of the task has changed to {new_status}")


class Agent(ABC):
    @abstractmethod
    async def handle(self, execution_context: ExecutionContext) -> StageResult: ...


class StoryWriter(Agent):
    async def handle(self, execution_context: ExecutionContext) -> StageResult:
        logger.debug("I the story writer received the story request event")
        execution_context.status = StageStatus.IN_PROGRESS
        await execution_context.notifier.send(
            "I have started the story writer",
        )
        return StageResult(
            status=StageStatus.COMPLETED,
            output="I have completed the story writer",
        )


agentRegistry: dict[str, Agent] = {
    "story-writer": StoryWriter(),
}


class ManagerNew:
    def __init__(self, target_room: str, sio: "AsyncServer") -> None:
        self.target_room = target_room
        self.sio = sio
        self.request_id = str(uuid.uuid4())
        self.plan: list[Stage] = self.build_plan()

    def package_communication_details(self) -> CommunicationDetails:
        return CommunicationDetails(
            request_id=self.request_id,
            sio=self.sio,
            target_room=self.target_room,
        )

    def build_plan(self) -> list[Stage]:
        communication_details = self.package_communication_details()
        return [
            Stage(
                task="Write a story about a cat",
                agent_type="story-writer",
            ),
        ]

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        logger.debug("Event Received", **event.data.model_dump())
        await self.notify_user()
        for stage in self.plan:
            agent = agentRegistry.get(stage.agent_type)
            if agent is None:
                logger.error(f"Agent {stage.agent_type} not found")
                continue
            result = await agent.handle(stage)
            stage.result = result
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
