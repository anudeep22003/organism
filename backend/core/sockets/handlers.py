from loguru import logger

from core.session import primary_session_manager
from core.sockets.types.envelope import AliasedBaseModel

from . import active_connections, sio

logger = logger.bind(name=__name__)


class Auth(AliasedBaseModel):
    session_id: str | None = None


@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> None:
    logger.debug("connection established")
    active_connections[sid] = environ
    auth_model = Auth.model_validate(auth)
    logger.debug(f"session_id: {auth_model.session_id}")
    logger.debug(f"# of active connections: {len(active_connections)}")

    session = primary_session_manager.get_session(
        session_id=auth_model.session_id,
        sid=sid,
        sio=sio,
        notify_user=True,
        dummy_mode=False,
    )
    target_room = session.get_target_room()
    await sio.enter_room(sid, target_room)
    logger.debug(f"joined room: {target_room}")
    logger.debug(f"session: {session}")


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
    primary_session_manager.remove_sid_from_session(sid)
