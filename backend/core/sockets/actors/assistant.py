from loguru import logger
from pydantic import Field

from core.common import AliasedBaseModel
from core.services.intelligence import ModelsEnum
from core.sockets.actors.base import BaseActor
from core.sockets.types.message import Message
from core.sockets.utils.streamer import stream_chunks_openai

from .. import sio

logger = logger.bind(name=__name__)


class AssistantRequest(AliasedBaseModel):
    history: list[Message] = Field(
        description="The conversation history between the user and the assistant so far"
    )


class AssistantActor(BaseActor[AssistantRequest]):
    def __init__(self) -> None:
        super().__init__(
            actor_name="assistant",
            stream_chunks=stream_chunks_openai,
            model=ModelsEnum.GPT_4O,
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
