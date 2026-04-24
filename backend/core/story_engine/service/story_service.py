import textwrap
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Protocol

from openai.types.chat import ChatCompletionChunk
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.intelligence.openai import async_openai_client

from ..events import ErrorPayload, EventEnvelope, EventType
from ..exceptions import (
    NotFoundError,
    NotOwnedError,
    StreamGeneratorError,
)
from ..models import EditEvent, Story
from ..models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from ..repository import Repository
from ..repository.exception import NotFoundError as RepoNotFoundError
from ..schemas.story import GenerateStoryRequest


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


@dataclass(frozen=True, slots=True)
class StoryStreamContext:
    """Parameters for executing a story stream."""

    story_id: uuid.UUID
    user_input_text: str  # original user instruction
    constructed_prompt: str  # prompt that is actually sent to the LLM
    edit_event_id: uuid.UUID


class StoryService:
    def __init__(
        self,
        db_session: AsyncSession,
        stream_generator: StoryStreamGenerator | None = None,
        processor: StreamProcessor | None = None,
    ):
        self.db = db_session
        self.repository = Repository(db_session)
        self.stream_generator = stream_generator or StoryStreamGenerator()
        self.processor = processor or OpenAIStreamProcessor()

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

    async def get_story(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> Story | None:
        return await self.repository.story.get_story(project_id, story_id)

    async def get_story_history(
        self, story_id: uuid.UUID, limit: int = 20
    ) -> list[EditEvent]:
        return await self.repository.edit_event.get_edit_events_for_target(
            target_type=EditEventTargetType.STORY, target_id=story_id, limit=limit
        )

    async def update_story(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        meta: dict | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Story:
        """Update meta, name, and/or description on a story.

        Only fields that are not None are written — omitted fields are untouched.
        Raises NotFoundError if the story does not exist in the given project.
        """
        try:
            story = await self.repository.story.update_story_meta_and_identity(
                project_id, story_id, meta=meta, name=name, description=description
            )
        except RepoNotFoundError as e:
            raise NotFoundError(str(e)) from e
        await self.db.commit()
        await self.db.refresh(story)
        return story

    async def generate_story(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        request: GenerateStoryRequest,
    ) -> AsyncIterator[EventEnvelope]:
        story_with_project = await self.repository.story.get_story_with_project(
            story_id
        )
        if story_with_project is None:
            raise NotFoundError(f"Story {story_id} not found")

        await self._check_story_ownership(user_id, story_with_project)

        prev_story_text = story_with_project.story_text

        # If story_text field is empty, then it is a refinement attempt
        is_refine = prev_story_text.strip() != ""
        operation = (
            EditEventOperationType.REFINE_STORY
            if is_refine
            else EditEventOperationType.GENERATE_STORY
        )

        # TX1: create edit event
        edit_event = await self.repository.edit_event.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.STORY,
            target_id=story_id,
            operation_type=operation,
            user_instruction=request.story_prompt,
        )
        await self.db.flush()  # assigns DB-generated id
        edit_event_id = edit_event.id
        await self.db.commit()

        if is_refine:
            constructed_prompt = self._build_refinement_prompt(
                prev_story_text, request.story_prompt
            )
        else:
            constructed_prompt = request.story_prompt

        params = StoryStreamContext(
            story_id=story_id,
            user_input_text=request.story_prompt,
            constructed_prompt=constructed_prompt,
            edit_event_id=edit_event_id,
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
                    # TX2: persist story + complete edit event atomically
                    async with self.db.begin_nested():
                        await self.repository.story.update_story_with_story_text_and_user_input_text(
                            params.story_id,
                            full_story,
                            params.user_input_text,
                            source_event_id=params.edit_event_id,
                        )
                        await self.repository.edit_event.update_edit_event(
                            params.edit_event_id,
                            EditEventStatus.SUCCEEDED,
                            output_snapshot={"storyText": full_story},
                        )
                    await self.db.commit()
                    break
        except Exception as e:
            await self.repository.edit_event.update_edit_event(
                params.edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            yield EventEnvelope(
                event_type=EventType.STREAM_ERROR,
                error=ErrorPayload(code="E_INTERNAL", message=str(e), retryable=True),
            )
            raise StreamGeneratorError(f"Error streaming story: {e}") from e
