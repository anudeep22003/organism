import json
import textwrap
import time
import uuid
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Protocol, cast

from fal_client.client import Status
from fastapi import UploadFile
from loguru import logger
from openai.types.chat import ChatCompletionChunk
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.intelligence import instructor_client
from core.services.intelligence.clients import async_openai_client
from core.services.intelligence.media_generator import fal_async_client

from ..events import ErrorPayload, EventEnvelope, EventType
from ..exceptions import (
    CharacterExtractorError,
    CharacterRefinementError,
    FalResponseError,
    InvalidUserIDError,
    NoStoryTextError,
    NotFoundError,
    NotOwnedError,
    StreamGeneratorError,
)
from ..models import (
    Character,
    Story,
)
from ..models.edit_event import EditEventStatus, OperationType, TargetType
from ..repository import NotFoundError as RepositoryNotFoundError
from ..repository import Repository
from ..schemas.story import GenerateStoryRequest
from ..state.character import CharacterBase as CharacterAttributes
from .dto_types import UploadReferenceImageDTO
from .image_upload import ImageUploadService


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
    user_input_text: str  # original user instruction
    constructed_prompt: str  # prompt that is actually sent to the LLM
    edit_event_id: uuid.UUID


class Service:
    def __init__(
        self,
        db_session: AsyncSession,
        repository: Repository | None = None,
        stream_generator: StoryStreamGenerator | None = None,
        processor: StreamProcessor | None = None,
        image_upload_service: ImageUploadService | None = None,
    ):
        self.repository = repository or Repository(db_session)
        self.stream_generator = stream_generator or StoryStreamGenerator()
        self.processor = processor or OpenAIStreamProcessor()
        self.image_upload_service = image_upload_service or ImageUploadService(
            repository=self.repository
        )

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

    def _build_character_refinement_prompt(
        self,
        story_text: str,
        character_attributes: dict[str, object],
        user_instruction: str,
    ) -> str:
        serialized_character = json.dumps(
            character_attributes, indent=2, sort_keys=True
        )
        return textwrap.dedent(f"""
            You are refining a character profile for a comic rendering system.
            Preserve the character's identity unless the instruction explicitly asks you to change it.
            Return a complete character profile with all fields filled in.

            User instruction:
            {user_instruction}

            Story context:
            {story_text}

            Current character profile:
            {serialized_character}
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
            user_input_text=request.story_prompt,
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
                    await self.repository.update_story_with_story_text_and_user_input_text(
                        params.story_id,
                        full_story,
                        params.user_input_text,
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

    async def extract_characters_from_story(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[Character]:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        if story.story_text.strip() == "":
            raise NoStoryTextError(
                f"Story {story_id} has no text, generate story first to extract characters"
            )

        extracted_characters = await self._extract_characters_from_story(
            story.story_text
        )

        # store characters in db
        characters = [
            Character(
                story_id=story_id,
                name=c.name,
                slug=slugify(c.name),
                attributes=c.model_dump(),
            )
            for c in extracted_characters
        ]
        await self.repository.bulk_create_characters(characters)

        created_characters = await self.repository.get_all_characters_for_a_story(
            story_id
        )

        return list(created_characters)

    async def _extract_characters_from_story(
        self, story_text: str
    ) -> list[CharacterAttributes]:
        try:
            response = await instructor_client.chat.completions.create(
                model="gpt-4o",
                response_model=list[CharacterAttributes],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a comic book writer. You will be given a story and you will need to extract the characters who affect the flow of the story.",
                    },
                    {"role": "user", "content": story_text},
                ],
            )
        except Exception as e:
            raise CharacterExtractorError(f"Error extracting characters: {e}") from e

        return response

    async def _refine_character_profile(
        self,
        story_text: str,
        character_id: uuid.UUID,
        character_attributes: dict[str, object],
        instruction: str,
    ) -> CharacterAttributes:
        prompt = self._build_character_refinement_prompt(
            story_text, character_attributes, instruction
        )
        try:
            return await instructor_client.chat.completions.create(
                model="gpt-4o",
                response_model=CharacterAttributes,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You refine character profiles for a comic generation "
                            "pipeline. Return the full updated profile."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as e:
            raise CharacterRefinementError(
                f"Error refining character {character_id}: {e}"
            ) from e

    async def get_story_characters(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[Character]:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        return await self.repository.get_all_characters_for_a_story(story_id)

    async def get_character(
        self, project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
    ) -> Character:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        character = await self.repository.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        return character

    async def update_character(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        updates: dict,
    ) -> Character:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        try:
            return await self.repository.update_character(
                character_id, story_id, updates
            )
        except RepositoryNotFoundError as e:
            raise NotFoundError(str(e)) from e

    async def refine_character(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        instruction: str,
    ) -> Character:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        # extract fields before they expire (ORM cost)
        story_text = story.story_text

        character = await self.repository.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        # extract fields before they expire (ORM cost)
        character_current_attributes = dict(character.attributes)

        edit_event = await self.repository.create_edit_event(
            project_id=project_id,
            target_type=TargetType.CHARACTER,
            target_id=character_id,
            operation_type=OperationType.REFINE_CHARACTER,
            user_instruction=instruction,
            input_snapshot=character_current_attributes,
        )
        edit_event_id = edit_event.id

        try:
            refined_profile = await self._refine_character_profile(
                story_text, character_id, character_current_attributes, instruction
            )
            refined_attributes = refined_profile.model_dump()
            refined_character = await self.repository.replace_character_attributes(
                character_id,
                story_id,
                refined_attributes,
                source_event_id=edit_event_id,
            )
            await self.repository.complete_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot=refined_character.attributes,
            )
            refreshed_character = await self.repository.get_character(
                character_id, story_id
            )
            if refreshed_character is None:
                raise NotFoundError(
                    f"Character {character_id} not found in story {story_id}"
                )
            return refreshed_character
        except Exception:
            await self.repository.complete_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            raise

    async def delete_character(
        self, project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
    ) -> None:
        story = await self.repository.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        try:
            await self.repository.delete_character(character_id, story_id)
        except RepositoryNotFoundError as e:
            raise NotFoundError(str(e)) from e

    def _build_character_render_prompt(
        self, character_attributes: dict[str, object]
    ) -> str:
        return textwrap.dedent(f"""
        Comic book character render (clean reference design).
        {json.dumps(character_attributes)}

        Style: modern comic book illustration, sharp line art, subtle halftone texture, high detail, consistent lighting.
        """).strip()

    async def _generate_image_render_response_and_time(
        self,
        prompt: str,
        on_queue_update: Callable[[Status], None] | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        try:
            response = await fal_async_client.subscribe(
                arguments={
                    "prompt": prompt,
                },
                on_queue_update=on_queue_update
                or (lambda status: print(f"Status: {status}")),
            )
        except Exception as e:
            raise FalResponseError(
                f"Error generating image render response: {e}"
            ) from e
        finally:
            end = time.perf_counter()
            logger.info(f"Time taken: {end - start} seconds")
            return response

    def _get_character_url_from_fal_client_response(self, response: dict) -> str:
        try:
            image_url = response.get("images", [])[0].get("url")
            if not image_url:
                raise FalResponseError("No image URL found in Fal client response")
            return cast(str, image_url)
        except json.JSONDecodeError as e:
            raise FalResponseError(f"Error parsing Fal client response: {e}") from e
        except KeyError as e:
            raise FalResponseError(
                f"No image URL found in Fal client response: {response}"
            ) from e

    async def render_character(
        self, project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
    ) -> Character:
        character = await self.repository.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )
        prompt = self._build_character_render_prompt(character.attributes)
        render_response = await self._generate_image_render_response_and_time(prompt)
        image_url = self._get_character_url_from_fal_client_response(render_response)
        character_with_render_url = await self.repository.update_character_render_url(
            character_id, story_id, image_url
        )
        return character_with_render_url

    async def upload_reference_image(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        image: UploadFile,
    ) -> None:
        dto = UploadReferenceImageDTO(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
            image=image.file,
        )
        await self.image_upload_service.upload_image(dto)
        return None
