from loguru import logger

from core.universe.timeline import SubscriptionKey, primary_timeline

from . import active_connections, sio

logger = logger.bind(name=__name__)


sid_to_session_id: dict[str, str] = {}
session_id_to_sid: dict[str, str] = {}
sid_to_subscription: dict[str, SubscriptionKey] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: dict) -> bool:
    _ = environ, auth
    logger.info("Socket connection rejected: sockets are currently disabled")
    return False


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
