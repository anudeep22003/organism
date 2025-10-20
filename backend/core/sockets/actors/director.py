import asyncio

from loguru import logger

from agents.types import DirectorRequest
from core.session import primary_session_manager
from core.sockets.types.envelope import Envelope
from core.universe.events import BaseEvent
from core.universe.timeline import primary_timeline

from .. import sio

logger = logger.bind(name=__name__)


@sio.on("c2s.director.stream.start")
async def handle_chat_stream_start(sid: str, envelope: dict) -> str:
    validated_envelope = Envelope[DirectorRequest].model_validate(envelope)
    logger.info(f"Director: received request: {validated_envelope.data.prompt}")

    session_id = primary_session_manager.get_session_id_from_sid(sid)
    target_room = primary_session_manager.get_target_room_from_session_id(session_id)

    new_task_event = BaseEvent[DirectorRequest](
        target_room=target_room,
        data=validated_envelope.data,
    )
    asyncio.create_task(primary_timeline.add_event(new_task_event))
    return "ack"
