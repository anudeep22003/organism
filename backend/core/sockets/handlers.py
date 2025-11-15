from loguru import logger

from core.auth.manager import JWTTokensManager, SessionManager
from core.services.database import async_session_maker
from core.sockets.types.envelope import AliasedBaseModel

from . import active_connections, sio

logger = logger.bind(name=__name__)


class Auth(AliasedBaseModel):
    session_id: str | None = None


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

    # logger.debug("connection established")
    # active_connections[sid] = environ
    # logger.debug(f"# of active connections: {len(active_connections)}")

    # # we get cookies as a raw string, so it needs to be manually parsed
    # cookies = {}
    # if "HTTP_COOKIE" in environ:
    #     cookie_header = environ["HTTP_COOKIE"]
    #     for cookie in cookie_header.split("; "):
    #         name, value = cookie.strip().split("=", 1)
    #         cookies[name] = value

    # session_token = cookies.get("session_token", None)
    # if not session_token:
    #     logger.debug("No session token found in cookies", sid=sid)
    #     return False
    # if not verify_session_token(session_token):
    #     logger.debug("Invalid session token", sid=sid)
    #     return False

    # session = primary_session_manager.get_or_create_session_for_token(
    #     session_token=session_token,
    #     sid=sid,
    #     sio=sio,
    #     notify_user=True,
    #     dummy_mode=False,
    # )
    # target_room = session.get_target_room()
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
    # del active_connections[sid]
    # primary_session_manager.remove_sid_from_session(sid)
