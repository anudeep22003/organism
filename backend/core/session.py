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

    def get_target_room(self) -> str:
        return f"session:{self.session_id}"


class SessionNotFoundError(Exception):
    def __init__(self, session_id: SessionId) -> None:
        super().__init__(f"Session {session_id} not found")


class SessionAlreadyExistsError(Exception):
    def __init__(self, session_id: SessionId) -> None:
        super().__init__(f"Session {session_id} already exists")


class SessionManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.sessions: dict[SessionId, Session] = {}
        self.sid_to_session: dict[str, Session] = {}

    def get_session(
        self,
        session_id: SessionId | None,
        sid: str,
        sio: "AsyncServer",
        notify_user: bool,
        dummy_mode: bool = False,
    ) -> Session:
        """Get or create a session. If session_id is None, a new session is created.
        If session_id is provided and the session exists, the sid is added to the session.
        If session_id is provided and the session does not exist, a new session is created with the given session id.

        Args:
            session_id (SessionId | None): The session id to get or create
            sid (str): The sid to add to the session
            sio (AsyncServer): The socketio server
            notify_user (bool): Whether to notify the user
            dummy_mode (bool, optional): Whether to run in dummy mode. Defaults to False.

        Returns:
            Session: The session
        """
        logger.debug(f"Current active sessions: {self.sessions.keys()}")
        if session_id is None:
            logger.debug("Creating new session")
            return self.create_new_session(
                session_id=session_id,
                sid=sid,
                sio=sio,
                notify_user=notify_user,
                dummy_mode=dummy_mode,
            )
        if session_id and session_id in self.sessions:
            logger.debug(f"Session {session_id} found, adding sid {sid}")
            return self.add_sid_to_session(session_id, sid)
        if session_id is not None and session_id not in self.sessions:
            logger.debug(
                f"Session {session_id} not found, creating new session with id: {session_id}"
            )
            return self.create_new_session(
                sid=sid,
                sio=sio,
                notify_user=notify_user,
                dummy_mode=dummy_mode,
                session_id=session_id,
            )

    def get_session_id_from_sid(self, sid: str) -> SessionId:
        if sid not in self.sid_to_session:
            raise SessionNotFoundError(sid)
        return self.sid_to_session[sid]
    
    def get_target_room_from_session_id(self, session_id: SessionId) -> str:
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)
        return self.sessions[session_id].get_target_room()

    def add_sid_to_session(self, session_id: SessionId, sid: str) -> Session:
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)
        session = self.sessions[session_id]
        session.sids.add(sid)
        self.sid_to_session[sid] = session_id
        return session

    def remove_sid_from_session(self, sid: str) -> None:
        if sid not in self.sid_to_session:
            raise SessionNotFoundError(sid)

        session_id = self.sid_to_session.pop(sid)
        logger.debug(f"removed sid: {sid} from sid_to_session")
        session = self.sessions[session_id]
        session.sids.discard(sid)
        logger.debug(f"Removed sid {sid} from session {session_id}")

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
        target_room = f"session:{session_id}"
        manager = Manager(
            target_room=target_room,
            sio=sio,
            notify_user=notify_user,
            dummy_mode=dummy_mode,
        )
        primary_timeline.subscribe(
            event_data_type=DirectorRequest,
            handler=manager.handle_event,
            target_room=target_room,
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
