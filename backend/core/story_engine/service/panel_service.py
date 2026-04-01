"""
PanelService — business logic for the panel pipeline.

Currently implements:
  - generate_panels: bulk generate all panels for a story from story text
  - generate_panel: single panel generate/regenerate
  - render_panel: render a panel image via fal
"""

import textwrap
import uuid
from io import BytesIO
from typing import Any

import httpx
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.intelligence import instructor_client
from core.services.intelligence.media_generator import fal_async_client

from ..exceptions import (
    FalResponseError,
    NoCharactersError,
    NoStoryTextError,
    NotFoundError,
)
from ..models import EditEvent, Panel
from ..models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from ..models.image import Image as ImageModel
from ..models.image import ImageContentType, ImageDiscriminatorKey
from ..repository import RepositoryV2
from ..schemas.panel import GeneratedPanelsResponse, PanelContent, PanelContentBase
from .image_service import GCSUploadService, extract_image_dimensions


class PanelService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repository_v2 = RepositoryV2(db_session)

    # -----------------------------------------------------------------------
    # generate_panels (bulk)
    # -----------------------------------------------------------------------

    async def generate_panels(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[Panel]:
        """Generate all panels for a story from its story text.

        Returns the persisted list of Panel ORM objects in order_index order.
        Per Decision 9: each panel gets its own EditEvent(GENERATE_PANEL, SUCCEEDED).
        Per Decision 3: character slugs in LLM output are resolved to character UUIDs.
        """
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        if story.story_text.strip() == "":
            raise NoStoryTextError(
                f"Story {story_id} has no text — generate the story first"
            )

        story_text = story.story_text

        # Load all characters to build slug → id mapping for resolution
        characters = await self.repository_v2.character.get_all_characters_for_a_story(
            story_id
        )
        slug_to_id: dict[str, uuid.UUID] = {c.slug: c.id for c in characters}

        if not slug_to_id:
            raise NoCharactersError(
                f"Story {story_id} has no characters — extract characters before generating panels"
            )

        # Call LLM to get structured panel content
        generated = await self._extract_panels_from_story(
            story_text, list(slug_to_id.keys())
        )

        panels: list[Panel] = []
        for order_index, panel_content in enumerate(generated.panels):
            panel = Panel.create(
                story_id=story_id,
                order_index=order_index,
                attributes={
                    "background": panel_content.background,
                    "dialogue": panel_content.dialogue,
                    "characters": panel_content.characters,
                },
            )
            await self.repository_v2.panel.create_panel(panel)
            await self.db.flush()  # assign panel.id before using it

            # Resolve slugs to character IDs and create join rows (Decision 3)
            for slug in panel_content.characters:
                character_id = slug_to_id.get(slug)
                if character_id is None:
                    logger.warning(
                        f"Panel generation: slug '{slug}' not found in story "
                        f"{story_id} characters — skipping join row"
                    )
                    continue
                await self.repository_v2.panel.create_panel_character(
                    panel_id=panel.id, character_id=character_id
                )

            # Per-panel EditEvent (Decision 9)
            edit_event = EditEvent.create_edit_event(
                project_id=project_id,
                target_type=EditEventTargetType.PANEL,
                target_id=panel.id,
                operation_type=EditEventOperationType.GENERATE_PANEL,
                user_instruction="",
                status=EditEventStatus.SUCCEEDED,
                output_snapshot=panel.attributes,
            )
            await self.repository_v2.edit_event.add_edit_event_to_db(edit_event)
            await self.db.flush()

            # Link panel to its source event
            panel.source_event_id = edit_event.id
            panels.append(panel)

        await self.db.commit()

        # Refresh all panels so their IDs and timestamps are up-to-date
        for panel in panels:
            await self.db.refresh(panel)

        return panels

    # -----------------------------------------------------------------------
    # generate_panel (single panel — Story 50)
    # -----------------------------------------------------------------------

    async def generate_panel(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        instruction: str | None,
    ) -> Panel:
        """Generate or regenerate content for a single panel (Decision 8).

        First call (empty attributes): generates from story context.
        Subsequent calls (populated attributes): refines using instruction.
        Operation type is always GENERATE_PANEL regardless.
        """
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        # Load characters to build slug list for constrained LLM extraction
        characters = await self.repository_v2.character.get_all_characters_for_a_story(
            story_id
        )
        character_slugs = [c.slug for c in characters]
        if not character_slugs:
            raise NoCharactersError(
                f"Story {story_id} has no characters — extract characters before generating panels"
            )

        # Snapshot all ORM attribute values before any commit (ORM objects expire after commit)
        input_attrs = dict(panel.attributes)
        panel_order_index = panel.order_index
        story_text = story.story_text

        # TX1: create PENDING edit event
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.GENERATE_PANEL,
            user_instruction=instruction or "",
            status=EditEventStatus.PENDING,
            input_snapshot=input_attrs,
        )
        await self.repository_v2.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            is_first_generation = not input_attrs
            if is_first_generation:
                panel_content = await self._generate_panel_first_time(
                    story_text=story_text,
                    order_index=panel_order_index,
                    character_slugs=character_slugs,
                )
            else:
                panel_content = await self._regenerate_panel(
                    existing_attributes=input_attrs,
                    instruction=instruction or "Regenerate this panel.",
                    character_slugs=character_slugs,
                )

            new_attributes = {
                "background": panel_content.background,
                "dialogue": panel_content.dialogue,
                "characters": panel_content.characters,
            }

            # TX2: update panel attributes + mark event SUCCEEDED
            panel.attributes = new_attributes
            panel.source_event_id = edit_event_id
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot=new_attributes,
            )
            await self.db.commit()
            await self.db.refresh(panel)
            return panel

        except Exception:
            await self.repository_v2.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    async def _generate_panel_first_time(
        self, story_text: str, order_index: int, character_slugs: list[str]
    ) -> PanelContent:
        """LLM call for first-time single panel generation."""
        from typing import Literal

        from pydantic import create_model

        CharacterSlug = Literal[tuple(character_slugs)]  # type: ignore[valid-type]
        ConstrainedPanelContent = create_model(
            "PanelContent",
            __base__=PanelContentBase,
            characters=(list[CharacterSlug], ...),  # type: ignore[valid-type]
        )

        slug_list = ", ".join(character_slugs)
        prompt = textwrap.dedent(f"""
            You are a comic book artist. Generate a single comic panel for panel #{order_index + 1}.

            Story:
            {story_text}

            Characters in this story (use exactly these slugs): {slug_list}

            Return a single panel with background description, dialogue, and character slugs.
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ConstrainedPanelContent,  # type: ignore[arg-type]
            messages=[
                {
                    "role": "system",
                    "content": "Generate a single comic panel from story context.",
                },
                {"role": "user", "content": prompt},
            ],
        )

    async def _regenerate_panel(
        self,
        existing_attributes: dict[str, Any],
        instruction: str,
        character_slugs: list[str],
    ) -> PanelContent:
        """LLM call for panel regeneration using existing attributes and instruction."""
        import json
        from typing import Literal

        from pydantic import create_model

        CharacterSlug = Literal[tuple(character_slugs)]  # type: ignore[valid-type]
        ConstrainedPanelContent = create_model(
            "PanelContent",
            __base__=PanelContentBase,
            characters=(list[CharacterSlug], ...),  # type: ignore[valid-type]
        )

        slug_list = ", ".join(character_slugs)
        prompt = textwrap.dedent(f"""
            You are a comic book artist. Refine this panel based on the instruction.

            Current panel:
            {json.dumps(existing_attributes, indent=2)}

            Instruction: {instruction}

            Characters in this story (use exactly these slugs): {slug_list}

            Return the updated panel.
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ConstrainedPanelContent,  # type: ignore[arg-type]
            messages=[
                {
                    "role": "system",
                    "content": "Refine a comic panel based on an instruction.",
                },
                {"role": "user", "content": prompt},
            ],
        )

    async def _extract_panels_from_story(
        self, story_text: str, character_slugs: list[str]
    ) -> GeneratedPanelsResponse:
        """Call instructor to extract structured panel content from story text.

        Builds a runtime-constrained Pydantic model so the LLM can only emit
        slugs that exist in the DB — prevents silent join-row mismatches.
        """
        from typing import Literal

        from pydantic import create_model

        CharacterSlug = Literal[tuple(character_slugs)]  # type: ignore[valid-type]
        ConstrainedPanelContent = create_model(
            "PanelContent",
            __base__=PanelContentBase,
            characters=(list[CharacterSlug], ...),  # type: ignore[valid-type]
        )
        ConstrainedResponse = create_model(
            "GeneratedPanelsResponse",
            panels=(list[ConstrainedPanelContent], ...),  # type: ignore[valid-type]
        )

        slug_list = ", ".join(character_slugs)
        prompt = textwrap.dedent(f"""
            You are a comic book artist and writer.
            Extract a list of comic book panels from the following story.
            For each panel provide:
              - background: a brief visual description of the setting/scene
              - dialogue: key spoken or thought dialogue in the panel (empty string if none)
              - characters: list of character slugs who appear — choose only from: {slug_list}

            Story:
            {story_text}
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ConstrainedResponse,  # type: ignore[arg-type]
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You extract structured comic panel data from story text. "
                        "Return well-structured panel descriptions suitable for illustration."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

    # -----------------------------------------------------------------------
    # get_panels (for Story 30)
    # -----------------------------------------------------------------------

    async def get_panels(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> list[tuple[Panel, Any]]:
        """Return all panels for a story with their canonical renders.

        Returns list[tuple[Panel, Image | None]] ordered by order_index.
        """
        from ..models.image import Image as ImageModel

        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panels = await self.repository_v2.panel.get_panels_for_story(story_id)

        result: list[tuple[Panel, ImageModel | None]] = []
        for panel in panels:
            render = await self.repository_v2.image.get_canonical_render(
                target_id=panel.id,
                discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
            )
            result.append((panel, render))

        return result

    # -----------------------------------------------------------------------
    # get_panel (for Story 40)
    # -----------------------------------------------------------------------

    async def get_panel(
        self, project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID
    ) -> tuple[Panel, Any]:
        """Return a single panel with its canonical render."""
        from ..models.image import Image as ImageModel

        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        render: ImageModel | None = await self.repository_v2.image.get_canonical_render(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )
        return panel, render

    # -----------------------------------------------------------------------
    # render_panel (Story 60)
    # -----------------------------------------------------------------------

    async def render_panel(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
    ) -> ImageModel:
        """Render a panel image via fal and store in GCS.

        Flow (Decision 16):
          1. Load the panel.
          2. Resolve character_render URLs for each character in the panel.
          3. Call fal with panel prompt + character image_urls.
          4. Download fal output bytes, upload to GCS.
          5. Create Image row (target_id=panel_id, discriminator_key=panel_render).
          6. Create EditEvent(RENDER_PANEL, SUCCEEDED).
          7. Return the Image ORM object.
        """
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        # Capture attribute values before any commit
        panel_attributes = dict(panel.attributes)

        # TX1: create PENDING edit event
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.RENDER_PANEL,
            user_instruction="",
            status=EditEventStatus.PENDING,
        )
        await self.repository_v2.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            # Resolve character renders for image_urls (Decision 16)
            character_ids = await self.repository_v2.panel.get_character_ids_for_panel(
                panel_id
            )
            gcs_service = GCSUploadService()
            image_urls: list[str] = []
            for character_id in character_ids:
                character_render = await self.repository_v2.image.get_canonical_render(
                    target_id=character_id,
                    discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
                )
                if character_render is None:
                    logger.warning(
                        f"Character {character_id} has no canonical render — "
                        f"skipping for panel {panel_id} render"
                    )
                    continue
                # Build a signed URL for the character render
                signed_url, _ = gcs_service.generate_signed_url(
                    character_render.object_key
                )
                image_urls.append(signed_url)

            # Build fal prompt from panel attributes
            prompt = self._build_panel_render_prompt(panel_attributes)

            # Call fal
            fal_response = await fal_async_client.subscribe(
                arguments={"prompt": prompt, "image_urls": image_urls},
                on_queue_update=lambda status: logger.debug(f"Fal status: {status}"),
            )
            fal_image_url = self._extract_fal_image_url(fal_response)

            # Download fal bytes and upload to GCS
            async with httpx.AsyncClient() as client:
                resp = await client.get(fal_image_url)
                resp.raise_for_status()
                image_bytes = BytesIO(resp.content)
                content_length = len(resp.content)
                raw_ct = (
                    resp.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                )
                valid_cts = {ct.value for ct in ImageContentType}
                content_type = (
                    ImageContentType(raw_ct)
                    if raw_ct in valid_cts
                    else ImageContentType.JPEG
                )

            # Parse dimensions from the image header (PIL lazy-open, < 1ms).
            # Raises if fal returned malformed bytes — propagates to FAILED edit event.
            width, height = extract_image_dimensions(image_bytes)  # resets seek to 0

            object_key = f"{project_id}/panel/{panel_id}/renders/{edit_event_id}"
            receipt = gcs_service.upload(object_key, image_bytes, content_type)

            # Create Image row
            image_model = ImageModel.create(
                project_id=project_id,
                user_id=user_id,
                target_id=panel_id,
                width=width,
                height=height,
                content_type=content_type,
                object_key=receipt.object_key,
                bucket=receipt.bucket,
                size_bytes=content_length,
                discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
                meta={},
            )
            await self.repository_v2.image.create_image(image_model)
            await self.db.flush()

            # TX2: complete edit event
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

    def _build_panel_render_prompt(self, panel_attributes: dict[str, Any]) -> str:
        background = panel_attributes.get("background", "")
        dialogue = panel_attributes.get("dialogue", "")
        prompt = f"Comic book panel. Scene: {background}"
        if dialogue:
            prompt += f" Dialogue: {dialogue}"
        prompt += (
            " Style: modern comic book illustration, sharp line art, vibrant colors."
        )
        return prompt

    def _extract_fal_image_url(self, response: dict) -> str:
        try:
            url = response.get("images", [])[0].get("url")
            if not url:
                raise FalResponseError("No image URL in fal response")
            return str(url)
        except (IndexError, KeyError) as e:
            raise FalResponseError(f"Unexpected fal response shape: {response}") from e

    # -----------------------------------------------------------------------
    # delete_panel (Story 110)
    # -----------------------------------------------------------------------

    async def delete_panel(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
    ) -> None:
        """Hard-delete a single panel.

        Steps:
        1. Verify the panel exists and belongs to the given story.
        2. Delete orphaned Image rows (discriminator_key=panel_render) — these
           use a polymorphic target_id with no DB FK so they are not cascade-
           deleted automatically (per raise_to_architect in Story 110).
        3. Delete the panel row — cascades panel_character rows via DB FK.
        """
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        # Explicit cleanup of polymorphic image rows (no DB FK cascade)
        await self.repository_v2.image.delete_images_for_target(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )

        await self.repository_v2.panel.delete_panel(panel_id, story_id)
        await self.db.commit()

    # -----------------------------------------------------------------------
    # get_panel_renders (Story 70)
    # -----------------------------------------------------------------------

    async def get_panel_renders(
        self, project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID
    ) -> list[ImageModel]:
        """Return all render Image rows for a panel, newest first."""
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        return await self.repository_v2.image.get_renders_for_target(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )

    # -----------------------------------------------------------------------
    # get_panel_history (for Story 80)
    # -----------------------------------------------------------------------

    async def get_panel_history(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        limit: int = 20,
    ) -> list[EditEvent]:
        """Return all edit events for a panel, ordered newest first."""
        story = await self.repository_v2.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository_v2.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        return await self.repository_v2.edit_event.get_edit_events_for_target(
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            limit=limit,
        )
