import json
import textwrap
import time
import uuid
from typing import Any, Callable, cast

from fal_client.client import Status
from fastapi import UploadFile
from loguru import logger
from slugify import slugify
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.intelligence import instructor_client
from core.services.intelligence.media_generator import fal_async_client

from ..exceptions import (
    CharacterExtractorError,
    CharacterRefinementError,
    FalResponseError,
    NoStoryTextError,
    NotFoundError,
)
from ..models import Character, EditEvent
from ..models.edit_event import EditEventStatus, OperationType, TargetType
from ..repository import NotFoundError as RepositoryNotFoundError
from ..repository import RepositoryV2
from ..state.character import CharacterBase as CharacterAttributes
from .dto_types import FileToUploadDTO, ProjectUserCharacterDTO, UploadReferenceImageDTO
from .image_upload import ImageUploadService


class CharacterService:
    def __init__(
        self,
        db_session: AsyncSession,
        image_upload_service: ImageUploadService | None = None,
    ):
        self.db = db_session
        self.repository_v2 = RepositoryV2(db_session)
        self.image_upload_service = image_upload_service or ImageUploadService(
            db=self.db, repository_v2=self.repository_v2
        )

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

    async def get_character_history(
        self, character_id: uuid.UUID, limit: int = 20
    ) -> list[EditEvent]:
        return await self.repository_v2.edit_event.get_edit_events_for_target(
            target_type=TargetType.CHARACTER, target_id=character_id, limit=limit
        )

    async def extract_characters_from_story(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[Character]:
        story = await self.repository_v2.story.get_story(project_id, story_id)
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
        await self.repository_v2.character.bulk_create_characters(characters)
        await self.db.commit()

        created_characters = (
            await self.repository_v2.character.get_all_characters_for_a_story(story_id)
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
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        return await self.repository_v2.character.get_all_characters_for_a_story(
            story_id
        )

    async def get_character(
        self, project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
    ) -> Character:
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        character = await self.repository_v2.character.get_character(
            character_id, story_id
        )
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
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        try:
            character = await self.repository_v2.character.update_character(
                character_id, story_id, updates
            )
            await self.db.commit()
            await self.db.refresh(character)
            return character
        except RepositoryNotFoundError as e:
            raise NotFoundError(str(e)) from e

    async def refine_character(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        instruction: str,
    ) -> Character:
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        # extract fields before they expire (ORM cost)
        story_text = story.story_text

        character = await self.repository_v2.character.get_character(
            character_id, story_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        # extract fields before they expire (ORM cost)
        character_current_attributes = dict(character.attributes)

        # TX1: create edit event
        edit_event = await self.repository_v2.edit_event.create_edit_event(
            project_id=project_id,
            target_type=TargetType.CHARACTER,
            target_id=character_id,
            operation_type=OperationType.REFINE_CHARACTER,
            user_instruction=instruction,
            input_snapshot=character_current_attributes,
        )
        await self.db.flush()  # assigns DB-generated id
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            # External work: LLM refinement
            refined_profile = await self._refine_character_profile(
                story_text, character_id, character_current_attributes, instruction
            )
            refined_attributes = refined_profile.model_dump()

            # TX2: persist refined attributes + complete edit event atomically
            async with self.db.begin_nested():
                refined_character = (
                    await self.repository_v2.character.replace_character_attributes(
                        character_id,
                        story_id,
                        refined_attributes,
                        source_event_id=edit_event_id,
                    )
                )
                await self.repository_v2.edit_event.update_edit_event(
                    edit_event_id,
                    EditEventStatus.SUCCEEDED,
                    output_snapshot=refined_character.attributes,
                )
            await self.db.commit()

            refreshed_character = await self.repository_v2.character.get_character(
                character_id, story_id
            )
            if refreshed_character is None:
                raise NotFoundError(
                    f"Character {character_id} not found in story {story_id}"
                )
            return refreshed_character
        except Exception:
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    async def delete_character(
        self, project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID
    ) -> None:
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        try:
            await self.repository_v2.character.delete_character(character_id, story_id)
            await self.db.commit()
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
            return response
        except Exception as e:
            raise FalResponseError(
                f"Error generating image render response: {e}"
            ) from e
        finally:
            end = time.perf_counter()
            logger.info(f"Time taken: {end - start} seconds")

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
        character = await self.repository_v2.character.get_character(
            character_id, story_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )
        prompt = self._build_character_render_prompt(character.attributes)
        render_response = await self._generate_image_render_response_and_time(prompt)
        image_url = self._get_character_url_from_fal_client_response(render_response)

        character_with_render_url = (
            await self.repository_v2.character.update_character_render_url(
                character_id, story_id, image_url
            )
        )
        await self.db.commit()
        await self.db.refresh(character_with_render_url)
        return character_with_render_url

    async def upload_reference_image(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        image: UploadFile,
    ) -> None:
        # allow user to give descriptive filename
        filename = slugify(image.filename) if image.filename else str(uuid.uuid4())

        dto = UploadReferenceImageDTO(
            file_to_upload=FileToUploadDTO(file=image.file, filename=filename),
            project_user_character=ProjectUserCharacterDTO(
                user_id=user_id,
                project_id=project_id,
                story_id=story_id,
                character_id=character_id,
            ),
        )
        await self.image_upload_service.upload_image(dto)
        return None
