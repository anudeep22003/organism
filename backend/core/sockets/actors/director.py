import asyncio
from dataclasses import replace
from datetime import datetime, timezone

from core.observation_manager import ObservationManager
from core.sockets.types.envelope import AliasedBaseModel, Envelope

from .. import sio


class DirectorRequest(AliasedBaseModel):
    prompt: str


@sio.on("c2s.director.stream.start")
async def handle_chat_stream_start(sid: str, envelope: dict) -> str:
    manager = ObservationManager()
    request = Envelope[DirectorRequest].model_validate(envelope)
    observation = manager.get_observation(sid)

    new_observation = replace(
        observation,
        user_prompt=request.data.prompt,
        updated_at=datetime.now(timezone.utc),
    )

    asyncio.create_task(manager.update_observation(sid, new_observation, sio))
    return "ack"
