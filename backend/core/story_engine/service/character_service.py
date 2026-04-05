import json
import textwrap
import time
import uuid
from io import BytesIO
from typing import Any, Callable, cast

import httpx
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
from ..models import Image as ImageModel
from ..models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from ..models.image import ImageContentType, ImageDiscriminatorKey
from ..repository import NotFoundError as RepositoryNotFoundError
from ..repository import RepositoryV2
from ..state.character import CharacterBase as CharacterAttributes
from .image_service import GCSUploadService, ImageService, extract_image_dimensions


class CharacterService:
    def __init__(
        self,
        db_session: AsyncSession,
        image_service: ImageService | None = None,
    ):
        self.db = db_session
        self.repository_v2 = RepositoryV2(db_session)
        self.image_service = image_service or ImageService(
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
            target_type=EditEventTargetType.CHARACTER,
            target_id=character_id,
            limit=limit,
        )

    async def get_character_renders(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> list[ImageModel]:
        """Return all character_render Image rows for a character, newest first.

        Raises NotFoundError if the character does not exist in the story.
        project_id is included in the signature for consistency with other
        character service methods, though the character → story → project
        ownership is validated via story_id.
        """
        character = await self.repository_v2.character.get_character(
            character_id, story_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )
        return await self.repository_v2.image.get_renders_for_target(
            target_id=character_id,
            discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
        )

    async def get_canonical_character_render(
        self, character_id: uuid.UUID
    ) -> ImageModel | None:
        """Return the most recent character_render Image for a character, or None."""
        return await self.repository_v2.image.get_canonical_render(
            target_id=character_id,
            discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
        )

    async def get_character_reference_images(
        self, character_id: uuid.UUID
    ) -> list[ImageModel]:
        """Return all reference images for a character, newest first.

        No ownership check — callers are responsible for verifying character
        access before calling this method.
        """
        return await self.repository_v2.image.get_character_reference_images(
            character_id
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
            target_type=EditEventTargetType.CHARACTER,
            target_id=character_id,
            operation_type=EditEventOperationType.REFINE_CHARACTER,
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
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> tuple[Character, ImageModel]:
        character = await self.repository_v2.character.get_character(
            character_id, story_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        # Snapshot attributes before external work
        character_attributes = dict(character.attributes)

        # TX1: create edit event
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.CHARACTER,
            target_id=character_id,
            operation_type=EditEventOperationType.RENDER_CHARACTER,
            user_instruction="",
            status=EditEventStatus.PENDING,
        )
        await self.repository_v2.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            prompt = self._build_character_render_prompt(character_attributes)
            render_response = await self._generate_image_render_response_and_time(
                prompt
            )
            fal_image_url = self._get_character_url_from_fal_client_response(
                render_response
            )

            # Download fal output bytes — fal URLs expire, we store in GCS for durability
            async with httpx.AsyncClient() as client:
                resp = await client.get(fal_image_url)
                resp.raise_for_status()
                image_bytes = BytesIO(resp.content)
                content_length = len(resp.content)
                # Detect content type from response header, default to JPEG
                raw_content_type = (
                    resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                )
                valid_content_types = {ct.value for ct in ImageContentType}
                content_type = (
                    ImageContentType(raw_content_type)
                    if raw_content_type in valid_content_types
                    else ImageContentType.JPEG
                )

            # Parse dimensions from the image header (PIL lazy-open, < 1ms).
            # Raises if fal returned malformed bytes — propagates to FAILED edit event.
            width, height = extract_image_dimensions(image_bytes)  # resets seek to 0

            # Upload to GCS
            gcs_service = GCSUploadService()
            object_key = (
                f"{project_id}/character/{character_id}/renders/{edit_event_id}"
            )
            receipt = gcs_service.upload(object_key, image_bytes, content_type)

            # Create Image row in the image table (Decision 5)
            image_model = ImageModel.create(
                project_id=project_id,
                user_id=user_id,
                target_id=character_id,
                width=width,
                height=height,
                content_type=content_type,
                object_key=receipt.object_key,
                bucket=receipt.bucket,
                size_bytes=content_length,
                discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
                meta={},
            )
            await self.repository_v2.image.create_image(image_model)
            await self.db.flush()

            # TX2: persist image row + complete edit event atomically
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot={"image_id": str(image_model.id)},
            )
            await self.db.commit()
            await self.db.refresh(image_model)

            refreshed_character = await self.repository_v2.character.get_character(
                character_id, story_id
            )
            if refreshed_character is None:
                raise NotFoundError(
                    f"Character {character_id} not found in story {story_id}"
                )
            return refreshed_character, image_model

        except Exception:
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    async def upload_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        image: UploadFile,
    ) -> ImageModel:
        return await self.image_service.upload_reference_image(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
            image_byte_stream=image.file,
        )

    async def render_character_edit(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        instruction: str,
        source_image_id: uuid.UUID,
    ) -> ImageModel:
        """Edit an existing character render via fal image-edit model.

        The source image is passed as a signed URL to fal alongside the user's
        instruction. A new Image row is created for the result; the source image
        is unchanged. The edit event records source_image_id so the audit trail
        is durable even after the signed URL expires.
        """
        character = await self.repository_v2.character.get_character_for_user_in_project_and_story(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found for user {user_id} in project {project_id}"
            )

        source_image = await self.repository_v2.image.get_image(source_image_id)
        if source_image is None or source_image.target_id != character_id:
            raise NotFoundError(
                f"Source image {source_image_id} not found for character {character_id}"
            )

        gcs_service = GCSUploadService()
        signed_url, _ = gcs_service.generate_signed_url(source_image.object_key)

        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.CHARACTER,
            target_id=character_id,
            operation_type=EditEventOperationType.RENDER_CHARACTER_EDIT,
            user_instruction=instruction,
            input_snapshot={"source_image_id": str(source_image_id)},
            status=EditEventStatus.PENDING,
        )
        await self.repository_v2.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            fal_response = await fal_async_client.subscribe(
                arguments={"prompt": instruction, "image_urls": [signed_url]},
                on_queue_update=lambda status: logger.info(f"Fal status: {status}"),
            )
            fal_image_url = self._get_character_url_from_fal_client_response(
                fal_response
            )

            async with httpx.AsyncClient() as client:
                resp = await client.get(fal_image_url)
                resp.raise_for_status()
                image_bytes = BytesIO(resp.content)
                content_length = len(resp.content)
                raw_content_type = (
                    resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                )
                valid_content_types = {ct.value for ct in ImageContentType}
                content_type = (
                    ImageContentType(raw_content_type)
                    if raw_content_type in valid_content_types
                    else ImageContentType.JPEG
                )

            width, height = extract_image_dimensions(image_bytes)

            object_key = (
                f"{project_id}/character/{character_id}/renders/{edit_event_id}"
            )
            receipt = gcs_service.upload(object_key, image_bytes, content_type)

            image_model = ImageModel.create(
                project_id=project_id,
                user_id=user_id,
                target_id=character_id,
                width=width,
                height=height,
                content_type=content_type,
                object_key=receipt.object_key,
                bucket=receipt.bucket,
                size_bytes=content_length,
                discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
                meta={},
            )
            await self.repository_v2.image.create_image(image_model)
            await self.db.flush()

            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot={"image_id": str(image_model.id)},
            )
            await self.db.commit()
            await self.db.refresh(image_model)
            return image_model

        except Exception:
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    async def delete_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        character = await self.repository_v2.character.get_character_for_user_in_project_and_story(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found for user {user_id} in project {project_id}"
            )
        try:
            await self.repository_v2.image.delete_reference_image(
                image_id, character_id
            )
            await self.db.commit()
        except RepositoryNotFoundError as e:
            raise NotFoundError(str(e)) from e
