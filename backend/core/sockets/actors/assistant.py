from typing import Literal

from loguru import logger
from pydantic import Field

from core.sockets.actors.base import BaseActor
from core.sockets.types.envelope import AliasedBaseModel
from core.sockets.types.message import Message
from core.sockets.utils.streamer import stream_chunks_openai

from .. import sio

logger = logger.bind(name=__name__)

MODEL: Literal["gpt-4o", "gpt-5"] = "gpt-4o"


class AssistantRequest(AliasedBaseModel):
    history: list[Message] = Field(
        description="The conversation history between the user and the assistant so far"
    )


class AssistantActor(BaseActor[AssistantRequest]):
    def __init__(self):
        super().__init__(
            actor_name="assistant", model=MODEL, stream_chunks=stream_chunks_openai
        )

    def prepare_messages(self, validated_request: AssistantRequest) -> list[Message]:
        return validated_request.history


@sio.on("c2s.assistant.stream.start")
async def handle_chat_stream_start(
    sid: str,
    envelope: dict,
) -> str:
    assistant_actor = AssistantActor()
    return assistant_actor.handle_stream_start(sid, envelope, AssistantRequest, sio)
