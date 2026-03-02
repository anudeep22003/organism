import textwrap
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from openai.types.chat import ChatCompletionChunk

from core.services.intelligence.clients import async_openai_client

from .events import ErrorPayload, EventEnvelope, EventType
from .exceptions import (
    InvalidUserIDError,
    NotFoundError,
    NotOwnedError,
    StreamGeneratorError,
)
from .models.edit_event import EditEventStatus, OperationType, TargetType
from .models.story import Story
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


@dataclass(frozen=True)
class StoryStreamContext:
    """Parameters for executing a story stream."""

    story_id: uuid.UUID
    user_instruction: str  # original user instruction
    constructed_prompt: str  # prompt that is actually sent to the LLM
    edit_event_id: uuid.UUID


class Service:
    def __init__(
        self,
        repository: Repository,
        stream_generator: StoryStreamGenerator | None = None,
        processor: StreamProcessor | None = None,
    ):
        self.repository = repository
        self.stream_generator = stream_generator or StoryStreamGenerator()
        self.processor = processor or OpenAIStreamProcessor()

    def _get_user_id(self, user_id: str) -> uuid.UUID:
        """
        Convert user ID string to UUID.

        Internal user_id is _user_id to avoid shadowing the parameter.
        It is always guaranteed to be a valid UUID.
        """
        try:
            return uuid.UUID(user_id)
        except ValueError as e:
            raise InvalidUserIDError(f"Invalid user ID: {user_id}") from e

    async def _check_story_ownership(
        self, _user_id: uuid.UUID, story_with_project: Story
    ) -> None:
        if story_with_project.project.user_id != _user_id:
            raise NotOwnedError(
                f"User {_user_id} does not own story {story_with_project.id}"
            )

    def _build_refinement_prompt(
        self, prev_story_text: str, user_instruction: str
    ) -> str:
        return textwrap.dedent(f"""
            You generated the previous story. The user is asking you to refine it according to the following instruction(s):
            {user_instruction}

            Here is the previous story:
            {prev_story_text}

            Please refine the previous story according to the user's instructions.
        """).strip()

    async def generate_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        request: GenerateStoryRequest,
    ) -> AsyncIterator[EventEnvelope]:
        _user_id = self._get_user_id(user_id)

        story_with_project = await self.repository.get_story_with_project(story_id)
        if story_with_project is None:
            raise NotFoundError(f"Story {story_id} not found")

        await self._check_story_ownership(_user_id, story_with_project)

        prev_story_text = story_with_project.story_text

        # If story_text field is empty, then it is a refinement attempt
        is_refine = prev_story_text.strip() != ""
        operation = (
            OperationType.REFINE_STORY if is_refine else OperationType.GENERATE_STORY
        )

        # Build a different prompt if the user is refining
        edit_event = await self.repository.create_edit_event(
            project_id=project_id,
            target_type=TargetType.STORY,
            target_id=story_id,
            operation_type=operation,
            user_instruction=request.story_prompt,
        )

        if is_refine:
            constructed_prompt = self._build_refinement_prompt(
                prev_story_text, request.story_prompt
            )
        else:
            constructed_prompt = request.story_prompt

        params = StoryStreamContext(
            story_id=story_id,
            user_instruction=request.story_prompt,
            constructed_prompt=constructed_prompt,
            edit_event_id=edit_event.id,
        )

        return self._execute_streaming(params)

    async def _execute_streaming(
        self, params: StoryStreamContext
    ) -> AsyncIterator[EventEnvelope]:
        accumulator: list[str] = []
        try:
            stream = await self.stream_generator.stream(params.constructed_prompt)
            async for chunk in stream:
                processed_chunk = await self.processor.process(chunk, accumulator)
                yield processed_chunk
                if processed_chunk.event_type == EventType.STREAM_END:
                    full_story = "".join(accumulator)
                    await self.repository.update_story_with_story_and_prompt(
                        params.story_id,
                        full_story,
                        params.user_instruction,
                        source_event_id=params.edit_event_id,
                    )
                    await self.repository.complete_edit_event(
                        params.edit_event_id,
                        EditEventStatus.SUCCEEDED,
                        output_snapshot={"storyText": full_story},
                    )
                    break
        except Exception as e:
            await self.repository.complete_edit_event(
                params.edit_event_id, EditEventStatus.FAILED
            )
            yield EventEnvelope(
                event_type=EventType.STREAM_ERROR,
                error=ErrorPayload(code="E_INTERNAL", message=str(e), retryable=True),
            )
            raise StreamGeneratorError(f"Error streaming story: {e}") from e
