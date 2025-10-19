from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.manager import Manager
from agents.types import DirectorRequest
from core.universe.timeline import SubscriptionKey, primary_timeline

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]


@dataclass(frozen=True)
class Session:
    manager: Manager
    timeline_subscription_key: SubscriptionKey


class SessionManager:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    def create_session(
        self, sid: str, sio: "AsyncServer", notify_user: bool
    ) -> Session:
        timeline_subscription_key = SubscriptionKey(DirectorRequest, sid)
        manager = Manager(sid=sid, sio=sio, notify_user=notify_user)
        primary_timeline.subscribe(
            event_data_type=DirectorRequest, handler=manager.handle_event, sid=sid
        )
        session = Session(
            manager=manager, timeline_subscription_key=timeline_subscription_key
        )
        self.sessions[sid] = session
        return session

    def get_session(self, sid: str, sio: "AsyncServer", notify_user: bool) -> Session:
        if sid not in self.sessions:
            return self.create_session(sid=sid, sio=sio, notify_user=notify_user)
        return self.sessions[sid]

    def destroy_session(self, sid: str) -> None:
        if sid in self.sessions:
            session = self.sessions.pop(sid)
            primary_timeline.unsubscribe(
                subscription_key=session.timeline_subscription_key
            )
            return session


primary_session_manager = SessionManager()
