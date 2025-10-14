from typing import TYPE_CHECKING

from core.event_queue import EventBus, ObservationUpdatedEvent
from core.observation import Observation
from core.singleton import SingletonMeta

if TYPE_CHECKING:
    from socketio import AsyncServer  # type: ignore[import-untyped]


class ObservationManager(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.event_bus = EventBus()
        self.observations: dict[str, Observation] = {}

    def get_observation(self, sid: str) -> Observation:
        if sid not in self.observations:
            self.observations[sid] = Observation()
        return self.observations[sid]

    async def update_observation(self, sid: str, observation: Observation, sio: "AsyncServer"):
        self.observations[sid] = observation
        await self.event_bus.publish(ObservationUpdatedEvent(sid, observation, sio))

    def delete_observation(self, sid: str):
        self.observations.pop(sid, None)
