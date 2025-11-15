from loguru import logger

from agents.manager import Manager
from agents.types import DirectorRequest
from core.auth.manager import JWTTokensManager, SessionManager
from core.services.database import async_session_maker
from core.sockets.types.envelope import AliasedBaseModel
from core.universe.timeline import primary_timeline

from . import active_connections, sio

logger = logger.bind(name=__name__)


class Auth(AliasedBaseModel):
    session_id: str | None = None


sid_to_session_id: dict[str, str] = {}
session_id_to_sid: dict[str, str] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> bool:
    logger.debug("auth received", auth=auth)

    jwt_manager = JWTTokensManager()

    #! add try blocks
    decoded = jwt_manager.decode_token(auth["accessToken"])
    user_id = decoded.get("sub")
    if not user_id:
        logger.debug("No user ID found in access token")
        return False
    if not isinstance(user_id, str):
        logger.debug("User ID is not a string")
        return False

    target_room = None

    async with async_session_maker() as async_db_session:
        session_manager = SessionManager(async_db_session=async_db_session)
        session = await session_manager.find_session_by_user_id(user_id)
        if not session:
            logger.debug("No session found for user", user_id=user_id)
            return False
        target_room = str(session.id)
        sid_to_session_id[sid] = target_room
        session_id_to_sid[target_room] = sid

    await sio.enter_room(sid, target_room)
    manager = Manager(
        target_room=target_room,
        sio=sio,
        notify_user=True,
        dummy_mode=False,
    )
    primary_timeline.subscribe(
        event_data_type=DirectorRequest,
        handler=manager.handle_event,
        target_room=target_room,
    )
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
    #! need to unsubscribe here
