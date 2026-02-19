import textwrap
import uuid
from typing import AsyncIterator, Protocol

from openai.types.chat import ChatCompletionChunk

from core.services.intelligence.clients import async_openai_client

from .events import EventEnvelope, EventType
from .exceptions import InvalidUserIDError, NotFoundError, NotOwnedError
from .repository import Repository
from .schemas.story import GenerateStoryRequest


class StoryStreamGenerator:
    """Low-level LLM streaming - pure generation, no state awareness."""

    async def stream(self, prompt: str) -> AsyncIterator[ChatCompletionChunk]:
        """Stream story chunks from LLM."""
        return await async_openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            temperature=0.7,
        )

    def _system_prompt(self) -> str:
        return textwrap.dedent("""
            You are a story teller.
            You understand the hero's journey and how to mould it to the story at play.
            You are a lover and a fighter, you understand the power of story to change the world.
            You know where to start the story, how to build tension, how to resolve the story, and how to keep the reader engaged.
            You are a master of the story arc, you know how to create a story that is both engaging and satisfying.
            You are a master at both telling fictionalized and real life stories.
            For real life stories you know to be faithful to history or mythology but are adept at knowing which creative liberties to take so that the original story and/or the feelings it evokes are still captured.
        """).strip()


class StreamProcessor(Protocol):
    async def process(
        self, chunk: ChatCompletionChunk, accumulator: list[str]
    ) -> EventEnvelope: ...


class OpenAIStreamProcessor(StreamProcessor):
    """Process OpenAI chat completion chunks."""

    async def process(
        self, chunk: ChatCompletionChunk, accumulator: list[str]
    ) -> EventEnvelope:
        if (content := chunk.choices[0].delta.content) is not None:
            if content == "":
                return EventEnvelope(
                    event_type=EventType.STREAM_START, payload={"delta": content}
                )
            else:
                accumulator.append(content)
                return EventEnvelope(
                    event_type=EventType.STREAM_CHUNK, payload={"delta": content}
                )
        if (finish_reason := chunk.choices[0].finish_reason) is not None:
            return EventEnvelope(
                event_type=EventType.STREAM_END,
                payload={"finish_reason": finish_reason},
            )
        raise ValueError(f"Unknown chunk: {chunk}")


class Service:
    def __init__(self, repository: Repository):
        self.repository = repository

    def _get_user_id(self, user_id: str) -> uuid.UUID:
        """
        Convert user ID string to UUID.

        Internal user_id is _user_id to avoid shadowing the parameter.
        It is always guaranteed to be a valid UUID.
        """
        try:
            return uuid.UUID(user_id)
        except ValueError:
            raise InvalidUserIDError(f"Invalid user ID: {user_id}")

    async def _check_story_ownership(
        self, _user_id: uuid.UUID, story_id: uuid.UUID
    ) -> None:
        story = await self.repository.get_story_with_project(story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")
        if story.project.user_id != _user_id:
            raise NotOwnedError(f"User {_user_id} does not own story {story_id}")

    async def generate_story(
        self, user_id: str, story_id: uuid.UUID, request: GenerateStoryRequest
    ) -> AsyncIterator[EventEnvelope]:
        _user_id = self._get_user_id(user_id)
        await self._check_story_ownership(_user_id, story_id)
        return self._execute_streaming(story_id, request.story_prompt)

    async def _execute_streaming(
        self,
        story_id: uuid.UUID,
        prompt: str,
        stream_generator: StoryStreamGenerator = StoryStreamGenerator(),
        processor: StreamProcessor = OpenAIStreamProcessor(),
    ) -> AsyncIterator[EventEnvelope]:
        accumulator: list[str] = []
        try:
            stream = await stream_generator.stream(prompt)
            async for chunk in stream:
                processed_chunk = await processor.process(chunk, accumulator)
                yield processed_chunk
                if processed_chunk.event_type == EventType.STREAM_END:
                    await self.repository.update_story_with_story_text_and_input_text(
                        story_id, "".join(accumulator), accumulator
                    )
                    break
        except Exception as e:
            yield EventEnvelope(
                event_type=EventType.STREAM_ERROR,
                payload={"error": str(e)},
            )
