import uuid
from typing import TYPE_CHECKING, Literal, cast

from loguru import logger
from pydantic import Field

from agents.types import DirectorRequest
from core.prompts.loader import load_prompt, load_prompt_list
from core.sockets.types.envelope import Actor, AliasedBaseModel
from core.sockets.types.intlligence_models import ModelsEnum
from core.sockets.types.message import Message
from core.sockets.utils.emit_helpers import (
    emit_text_start_chunk_end_events,
)
from core.sockets.utils.streamer import stream_chunks_openai
from core.universe.events import BaseEvent

if TYPE_CHECKING:
    from socketio import AsyncServer

logger = logger.bind(name=__name__)

TaskStatus = Literal["pending", "in_progress", "completed", "failed"]


class Task(AliasedBaseModel):
    order: int
    task: str
    status: TaskStatus = "pending"
    result: str = Field(default="")


class Manager:
    def __init__(
        self,
        target_room: str,
        sio: "AsyncServer",
        notify_user: bool,
        dummy_mode: bool = False,
    ) -> None:
        self.target_room = target_room
        self.sio = sio
        self.actor_name: Actor = "manager"
        self.model: ModelsEnum = ModelsEnum.GPT_4O
        self.task_list: list[Task] = []
        self.task_list_initialized: bool = False
        self.notify_user = notify_user
        self.dummy_mode = dummy_mode
        self.request_id = str(uuid.uuid4())

    def build_task_list(self, task: str) -> None:
        if self.task_list_initialized:
            return
        task_list = load_prompt_list("manager.yaml", "task_list")
        for order, task in enumerate(task_list):
            self.task_list.append(Task(order=order, task=task))
        self.task_list_initialized = True

    def prompt(self, key: Literal["task_list", "system_prompt"]) -> str | list[str]:
        if key == "task_list":
            return load_prompt_list("manager.yaml", "task_list")
        elif key == "system_prompt":
            return load_prompt("manager.yaml", "system_prompt")

    def get_next_task(
        self,
    ) -> Task | None:
        for task in self.task_list:
            if task.status != "completed":
                return task
        return None

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        self.build_task_list(event.data.prompt)
        next_task = self.get_next_task()
        if next_task is None:
            logger.debug("self: all tasks completed")
            return
        logger.debug("self: executing next task:", **next_task.model_dump())
        await self.handle_task(next_task, event)

    def prepare_messages(self, user_prompt: str, task: Task) -> list[Message]:
        system_prompt = self.prompt("system_prompt")
        return [
            Message(role="system", content=cast(str, system_prompt)),
            Message(role="user", content=f"Here is the user's request:\n{user_prompt}"),
            Message(role="user", content=f"Here is the current task:\n{task.task}"),
        ]

    async def update_task(
        self,
        task: Task,
        status: TaskStatus,
        result: str | None = None,
    ) -> None:
        """Update the task status and result. Notify the user if self.notify_user is True."""
        task.status = status
        task.result = result or ""
        if self.notify_user:
            await self.notify_user_of_task_update(task=task)
        logger.debug("self: updated task:", **task.model_dump())

    async def notify_user_of_task_update(self, task: Task) -> None:
        stream_id = str(uuid.uuid4())
        task_string = f"The task {task.task} status has changed to {task.status}."
        actor: Actor = "tasknotifier"
        await emit_text_start_chunk_end_events(
            sio=self.sio,
            target_room=self.target_room,
            actor=actor,
            request_id=self.request_id,
            stream_id=stream_id,
            text=task_string,
        )

    async def handle_task(self, task: Task, event: BaseEvent[DirectorRequest]) -> None:
        # update task status to in progress
        await self.update_task(
            task=task,
            status="in_progress",
        )
        stream_id = str(uuid.uuid4())
        messages = self.prepare_messages(event.data.prompt, task)
        result = await stream_chunks_openai(
            target_room=self.target_room,
            data=messages,
            request_id=self.request_id,
            stream_id=stream_id,
            actor=self.actor_name,
            model=self.model,
            sio=self.sio,
            dummy_mode=self.dummy_mode,
        )
        await self.update_task(
            task=task,
            status="completed",
            result=result,
        )
