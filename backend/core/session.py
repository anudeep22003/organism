import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING

from loguru import logger

from agents.manager import Manager
from agents.types import DirectorRequest
from core.singleton import SingletonMeta
from core.universe.timeline import SubscriptionKey, primary_timeline

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]

SessionId = str

logger = logger.bind(name=__name__)


@dataclass(frozen=True)
class Session:
    session_id: SessionId
    sids: set[str]
    timeline_subscription_key: SubscriptionKey
    manager: Manager


class SessionNotFoundError(Exception):
    def __init__(self, session_id: SessionId) -> None:
        super().__init__(f"Session {session_id} not found")


class SessionAlreadyExistsError(Exception):
    def __init__(self, session_id: SessionId) -> None:
        super().__init__(f"Session {session_id} already exists")


class SessionManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.sessions: dict[SessionId, Session] = {}

    def get_session(
        self,
        session_id: SessionId | None,
        sid: str,
        sio: "AsyncServer",
        notify_user: bool,
        dummy_mode: bool = False,
    ) -> Session:
        logger.debug("Current active sessions:", sessions=self.sessions.keys())
        if session_id is None:
            # create new session
            logger.debug("Creating new session")
            return self.create_new_session(
                session_id=session_id,
                sid=sid,
                sio=sio,
                notify_user=notify_user,
                dummy_mode=dummy_mode,
            )
        if session_id and session_id in self.sessions:
            # add sid to sessions
            # touch session (update time)
            logger.debug(f"Session {session_id} found, adding sid {sid}")
            return self.add_sid_to_session(session_id, sid)
        if session_id is not None and session_id not in self.sessions:
            # create a new session with the given session id
            logger.debug(f"Session {session_id} not found, creating new session")
            return self.create_new_session(
                sid=sid,
                sio=sio,
                notify_user=notify_user,
                dummy_mode=dummy_mode,
                session_id=session_id,
            )

    def add_sid_to_session(self, session_id: SessionId, sid: str) -> Session:
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)
        session = self.sessions[session_id]
        session.sids.add(sid)
        return session

    def create_new_session(
        self,
        sid: str,
        sio: "AsyncServer",
        notify_user: bool,
        session_id: SessionId | None = None,
        dummy_mode: bool = False,
    ) -> Session:
        logger.debug(f"Creating new session with id: {session_id}")
        if session_id is None:
            session_id = str(uuid.uuid4())
        logger.debug(f"Creating new session with id: {session_id}")
        timeline_subscription_key = SubscriptionKey(DirectorRequest, sid)
        manager = Manager(
            sid=sid, sio=sio, notify_user=notify_user, dummy_mode=dummy_mode
        )
        primary_timeline.subscribe(
            event_data_type=DirectorRequest, handler=manager.handle_event, sid=sid
        )
        session = Session(
            session_id=session_id,
            sids=set([sid]),
            timeline_subscription_key=timeline_subscription_key,
            manager=manager,
        )
        self.sessions[session_id] = session
        return session

    def destroy_session(self, sid: str) -> None:
        if sid in self.sessions:
            session = self.sessions.pop(sid)
            primary_timeline.unsubscribe(
                subscription_key=session.timeline_subscription_key
            )
            return session


primary_session_manager = SessionManager()
