from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

from loguru import logger

from core.sockets.types.envelope import Action, Actor, Direction, Envelope, Modifier

logger = logger.bind(name=__name__)

MODELS = Literal["gpt-4o", "gpt-5"]


async def emit_envelope(
    sio: "AsyncServer",
    sid: str,
    actor: Actor,
    modifier: Literal["start", "chunk", "end"],
    envelope: Envelope,
) -> None:
    await sio.emit(f"s2c.{actor}.stream.{modifier}", envelope.model_dump_json(), to=sid)
