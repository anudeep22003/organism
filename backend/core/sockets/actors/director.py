import asyncio

from agents.manager import Manager
from core.sockets.types.envelope import AliasedBaseModel, Envelope
from core.universe.timeline import primary_timeline 
from core.universe.events import BaseEvent

from .. import sio


class DirectorRequest(AliasedBaseModel):
    # context: str
    # output: str
    prompt: str

primary_timeline.subscribe(BaseEvent[DirectorRequest], Manager.handle_event)

@sio.on("c2s.director.stream.start")
async def handle_chat_stream_start(sid: str, envelope: dict) -> str:
    validated_envelope = Envelope[DirectorRequest].model_validate(envelope)
    new_task_event = BaseEvent[DirectorRequest](
        sid=sid,
        data=validated_envelope.data,
    )
    asyncio.create_task(primary_timeline.add_event(new_task_event))
    return "ack"
