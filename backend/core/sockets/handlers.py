from loguru import logger

from agents.manager import Manager
from agents.types import DirectorRequest
from core.auth import SessionManager
from core.auth.managers.jwt import JWTTokenManager
from core.common import AliasedBaseModel
from core.services.database import async_session_maker
from core.universe.timeline import SubscriptionKey, primary_timeline

from . import active_connections, sio

logger = logger.bind(name=__name__)


class Auth(AliasedBaseModel):
    session_id: str | None = None


sid_to_session_id: dict[str, str] = {}
session_id_to_sid: dict[str, str] = {}
sid_to_subscription: dict[str, SubscriptionKey] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> bool:
    logger.debug("auth received", auth=auth)
    if auth.get("accessToken") is None:
        logger.debug("No access token provided, closing connection")
        return False

    jwt_manager = JWTTokenManager()
    user_id = jwt_manager.extract_user_id_from_access_token(auth["accessToken"])
    target_room = None

    async with async_session_maker() as async_db_session:
        session_manager = SessionManager(db_session=async_db_session)
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
    subscription_key = primary_timeline.subscribe(
        event_data_type=DirectorRequest,
        handler=manager.handle_event,
        target_room=target_room,
    )
    sid_to_subscription[sid] = subscription_key
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

    # unsubscribe from timeline
    if sid in sid_to_subscription:
        sub_key = sid_to_subscription[sid]
        primary_timeline.unsubscribe(subscription_key=sub_key)

    if sid in sid_to_session_id:
        session_id = sid_to_session_id[sid]
        session_id_to_sid.pop(session_id)

    #! need to unsubscribe here
