from loguru import logger

from . import sio

logger = logger.bind(name=__name__)


@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> bool:
    _ = sid, environ, auth
    logger.info("Socket connection rejected: sockets are currently disabled")
    return False


@sio.event
async def disconnect(sid: str) -> None:
    logger.info("Socket disconnected", sid=sid)
