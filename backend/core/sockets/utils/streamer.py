import uuid
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

from core.sockets.types.envelope import Actor, Envelope
from core.sockets.types.message import Message

from .. import async_openai_client

MODELS = Literal["gpt-4o", "gpt-5"]


async def _emit_envelope(
    sio: "AsyncServer",
    sid: str,
    actor: Actor,
    modifier: Literal["start", "chunk", "end"],
    envelope: Envelope,
):
    await sio.emit(f"s2c.{actor}.stream.{modifier}", envelope.model_dump_json(), to=sid)


async def stream_chunks_static_text(sid: str, text: str, actor: Actor, sio: "AsyncServer") -> str:
    stream_id, request_id = str(uuid.uuid4()), str(uuid.uuid4())
    text_chunks = text.split("\n")

    await _emit_envelope(
        sio, sid, actor, "start",
        Envelope(request_id=request_id, stream_id=stream_id, seq=0, direction="s2c",
                 actor=actor, action="stream", modifier="start", data={"delta": "start"}),
    )

    for seq, chunk in enumerate(text_chunks):
        await _emit_envelope(
            sio, sid, actor, "chunk",
            Envelope(request_id=request_id, stream_id=stream_id, seq=seq, direction="s2c",
                     actor=actor, action="stream", modifier="chunk", data={"delta": chunk}),
        )

    await _emit_envelope(
        sio, sid, actor, "end",
        Envelope(request_id=request_id, stream_id=stream_id, seq=len(text_chunks), direction="s2c",
                 actor=actor, action="stream", modifier="end", data={"finish_reason": "stop"}),
    )

    return text


async def stream_chunks_openai(
    sid: str,
    data: list[Message],
    request_id: str,
    stream_id: str,
    actor: Actor,
    model: MODELS,
    sio: "AsyncServer",
) -> str:
    kwargs: dict[str, Any] = {"temperature": 0.7} if model == "gpt-4o" else {"reasoning_effort": "high"}

    stream = await async_openai_client.chat.completions.create(
        model=model,
        messages=[msg.to_openai_message() for msg in data],
        stream=True,
        **kwargs,
    )

    accumulated_content = ""
    seq = 0

    async for chunk in stream:
        seq += 1
        choice = chunk.choices[0]

        if choice.delta.content is not None:
            accumulated_content += choice.delta.content
            await _emit_envelope(
                sio, sid, actor, "chunk",
                Envelope(request_id=request_id, stream_id=stream_id, seq=seq, direction="s2c",
                         actor=actor, action="stream", modifier="chunk",
                         data={"delta": choice.delta.content}),
            )
        elif choice.finish_reason is not None:
            await _emit_envelope(
                sio, sid, actor, "end",
                Envelope(request_id=request_id, stream_id=stream_id, seq=seq, direction="s2c",
                         actor=actor, action="stream", modifier="end",
                         data={"finish_reason": choice.finish_reason}),
            )

    return accumulated_content
