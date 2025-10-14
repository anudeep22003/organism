import uuid
from dataclasses import replace
from typing import Literal

from core.event_queue import ObservationUpdatedEvent
from core.observation_manager import ObservationManager
from core.prompts.loader import load_prompt
from core.sockets.types.envelope import Actor, Envelope
from core.sockets.types.message import Message
from core.sockets.utils.streamer import stream_chunks_openai


class ScriptWriter:
    def __init__(self) -> None:
        self.actor_name: Actor = "scriptwriter"
        self.model: Literal["gpt-4o", "gpt-5"] = "gpt-4o"

    async def handle_observation_updated(self, event: ObservationUpdatedEvent):
        observation = event.observation

        if observation.user_prompt is None or observation.story is not None:
            return

        story = f"Consider this a story written by a scriptwriter, the user prompt is: {observation.user_prompt}"
        observation = replace(observation, story=story)

        await self._stream_story(event)
        await ObservationManager().update_observation(event.sid, observation, event.sio)

    async def _stream_story(self, event: ObservationUpdatedEvent):
        stream_id, request_id = str(uuid.uuid4()), str(uuid.uuid4())

        await event.sio.emit(
            f"s2c.{self.actor_name}.stream.start",
            Envelope(
                request_id=request_id,
                stream_id=stream_id,
                seq=0,
                direction="s2c",
                actor=self.actor_name,
                action="stream",
                modifier="start",
                data={"delta": "start"},
            ).model_dump_json(),
            to=event.sid,
        )

        messages = [
            Message(role="system", content=load_prompt("prompt_repo.yaml", "story_writing_prompt")),
            Message(role="user", content=event.observation.user_prompt or ""),
        ]

        await stream_chunks_openai(
            event.sid, messages, request_id, stream_id, self.actor_name, self.model, event.sio
        )


scriptwriter = ScriptWriter()
