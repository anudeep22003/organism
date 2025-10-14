from loguru import logger

from . import active_connections, sio

logger = logger.bind(name=__name__)


@sio.event
async def connect(sid: str, environ: dict) -> None:
    logger.info("connection established")
    active_connections[sid] = environ
    logger.info(f"# of active connections: {len(active_connections)}")


@sio.event
async def hello(sid: str, message: str) -> None:
    print(f"{sid}, {message}")
    await sio.emit(
        "hello",
        "number of active connections: " + str(len(active_connections)),
        to=sid,
    )


@sio.event
async def disconnect(sid: str) -> None:
    print(f"connection closed {sid}")
    del active_connections[sid]
