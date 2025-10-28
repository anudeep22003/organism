import uuid
from typing import TYPE_CHECKING, Any

from core.sockets.utils.emit_helpers import emit_envelope

if TYPE_CHECKING:
    from socketio import AsyncServer

from loguru import logger

from core.sockets.types.envelope import Actor, Envelope
from core.sockets.types.intlligence_models import ModelsEnum
from core.sockets.types.message import Message

from .. import async_openai_client

logger = logger.bind(name=__name__)


async def stream_chunks_static_text(
    target_room: str, request_id: str, text: str, actor: Actor, sio: "AsyncServer"
) -> str:
    stream_id = str(uuid.uuid4())
    text_chunks = text.split("\n")

    await emit_envelope(
        sio,
        target_room,
        actor,
        "start",
        Envelope(
            request_id=request_id,
            stream_id=stream_id,
            seq=0,
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="start",
            data={"delta": "start"},
        ),
    )

    for seq, chunk in enumerate(text_chunks):
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
                data={"delta": chunk},
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
            seq=len(text_chunks),
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="end",
            data={"finish_reason": "stop"},
        ),
    )

    return text


async def stream_chunks_openai(
    target_room: str,
    data: list[Message],
    request_id: str,
    stream_id: str,
    actor: Actor,
    model: ModelsEnum,
    sio: "AsyncServer",
    dummy_mode: bool = False,
) -> str:
    logger.info(f"Streamer: streaming chunks for {target_room} with data {data}")

    model_str = model.value

    if dummy_mode:
        return await stream_chunks_static_text(
            target_room, request_id, "This is a test stream", actor, sio
        )

    kwargs: dict[str, Any] = (
        {"temperature": 0.7} if model_str == "gpt-4o" else {"reasoning_effort": "high"}
    )

    # send start envelope
    await emit_envelope(
        sio,
        target_room,
        actor,
        "start",
        Envelope(
            request_id=request_id,
            stream_id=stream_id,
            direction="s2c",
            actor=actor,
            action="stream",
            modifier="start",
            data={"delta": "start"},
        ),
    )
    stream = await async_openai_client.chat.completions.create(
        model=model_str,
        messages=[msg.to_openai_message() for msg in data],
        stream=True,
        **kwargs,
    )

    accumulated_content = ""
    seq = 0

    async for chunk in stream:
        logger.trace(f"Streamer: streaming chunk {seq}")
        seq += 1
        choice = chunk.choices[0]

        if choice.delta.content is not None:
            accumulated_content += choice.delta.content
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
                    data={"delta": choice.delta.content},
                ),
            )
        elif choice.finish_reason is not None:
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
                    data={"finish_reason": choice.finish_reason},
                ),
            )

    return accumulated_content
