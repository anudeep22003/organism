import uuid
from typing import TYPE_CHECKING, Literal, cast

from loguru import logger
from pydantic import Field

from agents.types import DirectorRequest
from core.prompts.loader import load_prompt, load_prompt_list
from core.sockets.types.envelope import Actor, AliasedBaseModel, Envelope
from core.sockets.types.intlligence_models import ModelsEnum
from core.sockets.types.message import Message
from core.sockets.utils.emit_helpers import emit_envelope
from core.sockets.utils.streamer import stream_chunks_openai
from core.universe.events import BaseEvent

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

logger = logger.bind(name=__name__)

TaskStatus = Literal["pending", "in_progress", "completed", "failed"]


class Task(AliasedBaseModel):
    order: int
    task: str
    status: TaskStatus = "pending"
    result: str = Field(default="")


class Manager:
    def __init__(self, sid: str, sio: "AsyncServer", notify_user: bool) -> None:
        self.sid = sid
        self.sio = sio
        self.actor_name: Actor = "manager"
        self.model: ModelsEnum = ModelsEnum.GPT_4O
        self.task_list: list[Task] = []
        self.task_list_initialized: bool = False
        self.notify_user = notify_user

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
    ) -> Task:
        for task in self.task_list:
            if task.status != "completed":
                return task
        return None

    async def handle_event(self, event: BaseEvent[DirectorRequest]) -> None:
        self.build_task_list(event.data.prompt)
        next_task = self.get_next_task()
        if next_task is None:
            logger.info("self: all tasks completed")
            return
        logger.info("self: executing next task:", **next_task.model_dump())
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
        task.status = status
        task.result = result
        if self.notify_user:
            await self.notify_user_of_task_update(task=task)
        logger.info("self: updated task:", **task.model_dump())

    async def notify_user_of_task_update(self, task: Task) -> None:
        request_id, stream_id = str(uuid.uuid4()), str(uuid.uuid4())
        task_string = f"The task {task.task} status has changed to {task.status}."
        actor = "tasknotifier"
        start_envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            direction="s2c",
            seq=0,
            actor=actor,
            action="stream",
            modifier="start",
            data={"delta": "start"},
        )
        await emit_envelope(self.sio, self.sid, actor, "start", start_envelope)
        chunk_envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            direction="s2c",
            seq=0,
            actor=actor,
            action="stream",
            modifier="chunk",
            data={"delta": task_string},
        )
        await emit_envelope(self.sio, self.sid, actor, "chunk", chunk_envelope)
        end_envelope = Envelope(
            request_id=request_id,
            stream_id=stream_id,
            direction="s2c",
            seq=0,
            actor=actor,
            action="stream",
            modifier="end",
            data={"delta": "end"},
        )
        await emit_envelope(self.sio, self.sid, actor, "end", end_envelope)

    async def handle_task(self, task: Task, event: BaseEvent[DirectorRequest]) -> None:
        # update task status to in progress
        await self.update_task(
            task=task,
            status="in_progress",
        )
        request_id = str(uuid.uuid4())
        stream_id = str(uuid.uuid4())
        messages = self.prepare_messages(event.data.prompt, task)
        result = await stream_chunks_openai(
            sid=event.sid,
            data=messages,
            request_id=request_id,
            stream_id=stream_id,
            actor=self.actor_name,
            model=cast(Literal["gpt-4o", "gpt-5"], self.model.value),
            sio=self.sio,
            send_start=False,
            dummy_mode=True,
        )
        await self.update_task(
            task=task,
            status="completed",
            result=result,
        )
