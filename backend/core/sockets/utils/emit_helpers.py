from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

from loguru import logger

from core.sockets.types.envelope import Actor, Envelope

logger = logger.bind(name=__name__)

MODELS = Literal["gpt-4o", "gpt-5"]


async def emit_envelope(
    sio: "AsyncServer",
    target_room: str,
    actor: Actor,
    modifier: Literal["start", "chunk", "end"],
    envelope: Envelope,
) -> None:
    await sio.emit(
        f"s2c.{actor}.stream.{modifier}", envelope.model_dump_json(), to=target_room
    )


async def emit_text_start_chunk_end_events(
    sio: "AsyncServer",
    target_room: str,
    actor: Actor,
    request_id: str,
    stream_id: str,
    text: str,
) -> None:
    seq = 0
    await emit_envelope(
        sio,
        target_room,
        actor,
        "start",
        Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=seq,
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="start",
            data={"delta": "start"},
        ),
    )
    await emit_envelope(
        sio,
        target_room,
        actor,
        "chunk",
        Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=seq,
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="chunk",
            data={"delta": text},
        ),
    )
    await emit_envelope(
        sio,
        target_room,
        actor,
        "end",
        Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=seq,
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="end",
            data={"delta": "end"},
        ),
    )
