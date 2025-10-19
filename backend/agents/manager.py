import uuid
from typing import TYPE_CHECKING, Literal, cast

from attr import dataclass
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


@dataclass
class NotifyPayload:
    sid: str
    sio: "AsyncServer"


class Task(AliasedBaseModel):
    order: int
    task: str
    status: TaskStatus = "pending"
    result: str = Field(default="")


class Manager:
    actor_name: Actor = "manager"
    model: ModelsEnum = ModelsEnum.GPT_4O
    task_list: list[Task] = []
    task_list_initialized: bool = False

    @staticmethod
    def build_task_list(task: str) -> None:
        if Manager.task_list_initialized:
            return
        task_list = load_prompt_list("manager.yaml", "task_list")
        for order, task in enumerate(task_list):
            Manager.task_list.append(Task(order=order, task=task))
        Manager.task_list_initialized = True

    @staticmethod
    def prompt(key: Literal["task_list", "system_prompt"]) -> str | list[str]:
        if key == "task_list":
            return load_prompt_list("manager.yaml", "task_list")
        elif key == "system_prompt":
            return load_prompt("manager.yaml", "system_prompt")
        else:
            raise ValueError(f"Invalid key: {key}")

    @staticmethod
    def get_next_task() -> Task:
        for task in Manager.task_list:
            if task.status != "completed":
                return task
        return None

    @staticmethod
    async def handle_event(event: BaseEvent[DirectorRequest]) -> None:
        Manager.build_task_list(event.data.prompt)
        next_task = Manager.get_next_task()
        if next_task is None:
            logger.info("Manager: all tasks completed")
            return
        logger.info("Manager: executing next task:", **next_task.model_dump())
        await Manager.handle_task(next_task, event)

    @staticmethod
    def prepare_messages(user_prompt: str, task: Task) -> list[Message]:
        system_prompt = Manager.prompt("system_prompt")
        return [
            Message(role="system", content=cast(str, system_prompt)),
            Message(role="user", content=f"Here is the user's request:\n{user_prompt}"),
            Message(role="user", content=f"Here is the current task:\n{task.task}"),
        ]

    @staticmethod
    async def update_task(
        task: Task,
        status: TaskStatus,
        result: str | None = None,
        notify: NotifyPayload | None = None,
    ) -> None:
        task.status = status
        task.result = result
        if notify is not None:
            await Manager.notify_user_of_task_update(
                task=task, sid=notify.sid, sio=notify.sio
            )
        logger.info("Manager: updated task:", **task.model_dump())

    @staticmethod
    async def notify_user_of_task_update(
        task: Task, sid: str, sio: "AsyncServer"
    ) -> None:
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
        await emit_envelope(sio, sid, actor, "start", start_envelope)
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
        await emit_envelope(sio, sid, actor, "chunk", chunk_envelope)
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
        await emit_envelope(sio, sid, actor, "end", end_envelope)

    @staticmethod
    async def handle_task(task: Task, event: BaseEvent[DirectorRequest]) -> None:
        # update task status to in progress
        await Manager.update_task(
            task=task,
            status="in_progress",
            notify=NotifyPayload(sid=event.sid, sio=event.sio),
        )
        request_id = str(uuid.uuid4())
        stream_id = str(uuid.uuid4())
        messages = Manager.prepare_messages(event.data.prompt, task)
        result = await stream_chunks_openai(
            sid=event.sid,
            data=messages,
            request_id=request_id,
            stream_id=stream_id,
            actor=Manager.actor_name,
            model=cast(Literal["gpt-4o", "gpt-5"], Manager.model.value),
            sio=event.sio,
            send_start=False,
            dummy_mode=True,
        )
        await Manager.update_task(
            task=task,
            status="completed",
            result=result,
            notify=NotifyPayload(sid=event.sid, sio=event.sio),
        )
