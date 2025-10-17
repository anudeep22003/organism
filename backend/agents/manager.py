from typing import Literal, cast
import uuid
from loguru import logger
from core.prompts.loader import load_prompt_list, load_prompt
from core.sockets.types.envelope import Actor
from core.sockets.types.intlligence_models import ModelsEnum
from core.sockets.types.message import Message
from core.sockets.utils.streamer import stream_chunks_openai
from core.universe.events import BaseEvent
from agents.types import DirectorRequest

logger = logger.bind(name=__name__)


class Manager:
    actor_name: Actor = "manager"
    model: ModelsEnum = ModelsEnum.GPT_4O

    @staticmethod
    def prompt(key: Literal["task_list", "system_prompt"]) -> str | list[str]:
        if key == "task_list":
            return load_prompt_list("manager.yaml", "task_list")
        elif key == "system_prompt":
            return load_prompt("manager.yaml", "system_prompt")
        else:
            raise ValueError(f"Invalid key: {key}")
    
    @staticmethod
    async def handle_event(event: BaseEvent[DirectorRequest]) -> None:
        logger.info(f"Manager: handling event: {event}")
        system_prompt = Manager.prompt("system_prompt")
        task_list = Manager.prompt("task_list")
        stream_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        for task in task_list:
            logger.info(f"Manager: executing task: {task}")
            messages = [
                Message(role="system", content=cast(str, system_prompt)),
                Message(role="user", content=f"Here is the user's request: {event.data.prompt}"),
                Message(role="user", content=f"Here is the task: {task}"),
            ]
            logger.info(f"Manager: executing task: {task}")
            await stream_chunks_openai(
                sid=event.sid,
                data=messages,
                request_id=request_id,
                stream_id=stream_id,
                actor=Manager.actor_name,
                model=cast(Literal["gpt-4o", "gpt-5"], Manager.model.value),
                sio=event.sio,
                send_start=True,
            )