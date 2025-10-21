from loguru import logger

from core.auth import verify_session_token
from core.session import primary_session_manager
from core.sockets.types.envelope import AliasedBaseModel

from . import active_connections, sio

logger = logger.bind(name=__name__)


class Auth(AliasedBaseModel):
    session_id: str | None = None


@sio.event
async def connect(sid: str, environ: dict) -> bool:
    logger.debug("connection established")
    active_connections[sid] = environ
    logger.debug(f"# of active connections: {len(active_connections)}")

    # we get cookies as a raw string, so it needs to be manually parsed
    cookies = {}
    if "HTTP_COOKIE" in environ:
        cookie_header = environ["HTTP_COOKIE"]
        for cookie in cookie_header.split("; "):
            name, value = cookie.strip().split("=", 1)
            cookies[name] = value

    session_token = cookies.get("session_token", None)
    if not session_token:
        logger.debug("No session token found in cookies", sid=sid)
        return False
    if not verify_session_token(session_token):
        logger.debug("Invalid session token", sid=sid)
        return False

    session = primary_session_manager.get_session(
        session_id=session_token,
        sid=sid,
        sio=sio,
        notify_user=True,
        dummy_mode=False,
    )
    target_room = session.get_target_room()
    await sio.enter_room(sid, target_room)
    logger.debug(f"joined room: {target_room}")
    logger.debug(f"session: {session}")
    return True


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
