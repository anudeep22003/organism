import asyncio

from agents.manager import Manager
from core.sockets.types.envelope import AliasedBaseModel, Envelope
from core.universe.timeline import primary_timeline 
from core.universe.events import BaseEvent
from agents.types import DirectorRequest

from .. import sio
from loguru import logger

logger = logger.bind(name=__name__)


primary_timeline.subscribe(BaseEvent[DirectorRequest], Manager.handle_event)

@sio.on("c2s.director.stream.start")
async def handle_chat_stream_start(sid: str, envelope: dict) -> str:
    validated_envelope = Envelope[DirectorRequest].model_validate(envelope)
    logger.info(f"Director: received request: {validated_envelope.data.prompt}")
    new_task_event = BaseEvent[DirectorRequest](
        sid=sid,
        sio=sio,
        data=validated_envelope.data,
    )
    asyncio.create_task(primary_timeline.add_event(new_task_event))
    return "ack"
