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
from fastapi import UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.intelligence import instructor_client
from core.infrastructure.intelligence.media_generator import fal_async_client

from ..exceptions import (
    FalResponseError,
    NoCharactersError,
    NoStoryTextError,
    NotFoundError,
    PanelAlreadyGeneratedError,
)
from ..models import EditEvent, Panel
from ..models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from ..models.image import Image as ImageModel
from ..models.image import ImageContentType, ImageDiscriminatorKey
from ..repository import Repository
from ..schemas.panel import GeneratedPanelsResponse, PanelContent, PanelContentBase
from ..storage_keys import panel_render_key
from .image_service import (
    ImageService,
    extract_image_dimensions,
    get_gcs_upload_service,
)


class PanelService:
    def __init__(
        self,
        db_session: AsyncSession,
        image_service: ImageService | None = None,
    ):
        self.db = db_session
        self.repository = Repository(db_session)
        self.image_service = image_service or ImageService(
            db=self.db, repository=self.repository
        )

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
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        if story.story_text.strip() == "":
            raise NoStoryTextError(
                f"Story {story_id} has no text — generate the story first"
            )

        story_text = story.story_text

        # Load all characters to build slug → id mapping for resolution
        characters = await self.repository.character.get_all_characters_for_a_story(
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
            await self.repository.panel.create_panel(panel)
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
                await self.repository.panel.create_panel_character(
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
            await self.repository.edit_event.add_edit_event_to_db(edit_event)
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
    ) -> Panel:
        """Generate content for a single panel for the first time.

        Only valid when the panel has no content yet (empty attributes).
        Raises PanelAlreadyGeneratedError if the panel already has content —
        callers should use /refine to update an already-generated panel.

        Creates panel_character join rows for each character the LLM assigns,
        mirroring the bulk generate_panels flow.
        """
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        # Guard: first-generation only
        if panel.attributes:
            raise PanelAlreadyGeneratedError(
                f"Panel {panel_id} already has content — use /refine to update it"
            )

        # Load characters to build slug list for constrained LLM extraction
        characters = await self.repository.character.get_all_characters_for_a_story(
            story_id
        )
        slug_to_id: dict[str, uuid.UUID] = {c.slug: c.id for c in characters}
        character_slugs = list(slug_to_id.keys())
        if not character_slugs:
            raise NoCharactersError(
                f"Story {story_id} has no characters — extract characters before generating panels"
            )

        # Snapshot order_index and story_text before any commit
        panel_order_index = panel.order_index
        story_text = story.story_text

        # TX1: create PENDING edit event
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.GENERATE_PANEL,
            user_instruction="",
            status=EditEventStatus.PENDING,
            input_snapshot={},
        )
        await self.repository.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            panel_content = await self._generate_panel_first_time(
                story_text=story_text,
                order_index=panel_order_index,
                character_slugs=character_slugs,
            )
            new_attributes = {
                "background": panel_content.background,
                "dialogue": panel_content.dialogue,
                "characters": panel_content.characters,
            }

            # TX2: update panel attributes + create join rows + mark event SUCCEEDED
            panel.attributes = new_attributes
            panel.source_event_id = edit_event_id
            resolved_ids = [
                slug_to_id[slug]
                for slug in panel_content.characters
                if slug in slug_to_id
            ]
            await self.repository.panel.replace_panel_characters(panel_id, resolved_ids)
            await self.repository.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot=new_attributes,
            )
            await self.db.commit()
            await self.db.refresh(panel)
            return panel

        except Exception:
            await self.repository.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    # -----------------------------------------------------------------------
    # refine_panel (user-directed attribute update — Story 55)
    # -----------------------------------------------------------------------

    async def refine_panel(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        instruction: str,
    ) -> Panel:
        """Refine a panel's attributes using a user instruction.

        Requires the panel to have already been generated (non-empty attributes).
        Calls the LLM regeneration branch with the provided instruction and
        persists the updated attributes under a REFINE_PANEL edit event.
        Mirrors refine_character in character_service.py.
        """
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        input_attrs = dict(panel.attributes)
        if not input_attrs:
            raise NotFoundError(
                f"Panel {panel_id} has no content yet — generate it before refining"
            )

        characters = await self.repository.character.get_all_characters_for_a_story(
            story_id
        )
        slug_to_id: dict[str, uuid.UUID] = {c.slug: c.id for c in characters}
        character_slugs = list(slug_to_id.keys())
        if not character_slugs:
            raise NoCharactersError(
                f"Story {story_id} has no characters — extract characters first"
            )

        # TX1: create PENDING edit event
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.REFINE_PANEL,
            user_instruction=instruction,
            status=EditEventStatus.PENDING,
            input_snapshot=input_attrs,
        )
        await self.repository.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            panel_content = await self._regenerate_panel(
                existing_attributes=input_attrs,
                instruction=instruction,
                character_slugs=character_slugs,
            )
            new_attributes = {
                "background": panel_content.background,
                "dialogue": panel_content.dialogue,
                "characters": panel_content.characters,
            }

            # TX2: persist refined attributes + reconcile join table + mark SUCCEEDED
            panel.attributes = new_attributes
            panel.source_event_id = edit_event_id
            resolved_ids = [
                slug_to_id[slug]
                for slug in panel_content.characters
                if slug in slug_to_id
            ]
            await self.repository.panel.replace_panel_characters(panel_id, resolved_ids)
            await self.repository.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot=new_attributes,
            )
            await self.db.commit()
            await self.db.refresh(panel)
            return panel

        except Exception:
            await self.repository.edit_event.update_edit_event(
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
    # get_canonical_panel_render
    # -----------------------------------------------------------------------

    async def get_canonical_panel_render(
        self, panel_id: uuid.UUID
    ) -> ImageModel | None:
        """Return the canonical render for a panel.

        Prefers canonical_render_id if explicitly set on the panel; falls back
        to the most-recently created PANEL_RENDER image when the pointer is NULL.
        Mirrors get_canonical_character_render in character_service.py.
        """
        panel = await self.repository.panel.get_panel_by_id(panel_id)
        if panel is not None and panel.canonical_render_id is not None:
            return await self.repository.image.get_image(panel.canonical_render_id)
        return await self.repository.image.get_canonical_render(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )

    # -----------------------------------------------------------------------
    # set_canonical_render (explicit user override)
    # -----------------------------------------------------------------------

    async def set_canonical_render(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> Panel:
        """Set a specific render as the canonical render for a panel.

        Verifies story/panel ownership and that the image is a PANEL_RENDER
        belonging to this panel. Creates a SET_CANONICAL_RENDER audit event
        immediately as SUCCEEDED (no PENDING state). Returns the updated panel.
        """
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found in project {project_id}")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        image = await self.repository.image.get_image(image_id)
        if (
            image is None
            or image.target_id != panel_id
            or image.discriminator_key != ImageDiscriminatorKey.PANEL_RENDER
        ):
            raise NotFoundError(
                f"Render image {image_id} not found for panel {panel_id}"
            )

        await self.repository.panel.set_canonical_render(panel_id, story_id, image_id)

        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.SET_CANONICAL_RENDER,
            user_instruction="",
            input_snapshot={"image_id": str(image_id)},
            status=EditEventStatus.SUCCEEDED,
        )
        await self.repository.edit_event.add_edit_event_to_db(edit_event)

        await self.db.commit()
        await self.db.refresh(panel)
        return panel

    # -----------------------------------------------------------------------
    # Reference image upload / retrieval
    # -----------------------------------------------------------------------

    async def upload_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        image: UploadFile,
    ) -> ImageModel:
        """Upload a reference image for a panel.

        Delegates to ImageService.upload_panel_reference_image which handles
        GCS upload, Image row creation, and UPLOAD_REFERENCE_IMAGE audit event.
        """
        return await self.image_service.upload_panel_reference_image(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            image_byte_stream=image.file,
        )

    async def get_panel_reference_images(self, panel_id: uuid.UUID) -> list[ImageModel]:
        """Return all PANEL_REFERENCE images for a panel, newest first."""
        return await self.repository.image.get_panel_reference_images(panel_id)

    async def delete_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        image_id: uuid.UUID,
    ) -> None:
        """Delete a PANEL_REFERENCE image from a panel.

        Verifies the panel exists in the given story/project, then delegates
        deletion to the image repository which validates target ownership and
        discriminator before deleting.
        """
        from ..repository.exception import NotFoundError as RepositoryNotFoundError

        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found in project {project_id}")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        try:
            await self.repository.image.delete_panel_reference_image(image_id, panel_id)
            await self.db.commit()
        except RepositoryNotFoundError as e:
            raise NotFoundError(str(e)) from e

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

        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panels = await self.repository.panel.get_panels_for_story(story_id)

        result: list[tuple[Panel, ImageModel | None]] = []
        for panel in panels:
            render = await self.get_canonical_panel_render(panel.id)
            result.append((panel, render))

        return result

    # -----------------------------------------------------------------------
    # get_panel (for Story 40)
    # -----------------------------------------------------------------------

    async def get_panel(
        self, project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID
    ) -> tuple[Panel, Any]:
        """Return a single panel with its canonical render."""

        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        render = await self.get_canonical_panel_render(panel_id)
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
    ) -> tuple[Panel, ImageModel]:
        """Render a panel image via fal and store in GCS.

        Flow (Decision 16):
          1. Load the panel.
          2. Resolve character_render URLs for each character in the panel.
          3. Call fal with panel prompt + character image_urls.
          4. Download fal output bytes, upload to GCS.
          5. Create Image row (target_id=panel_id, discriminator_key=panel_render).
          6. Create EditEvent(RENDER_PANEL, SUCCEEDED).
          7. Return (panel, image) — mirrors render_character return signature.
        """
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
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
        await self.repository.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            # Resolve character renders for image_urls (Decision 16)
            character_ids = await self.repository.panel.get_character_ids_for_panel(
                panel_id
            )
            gcs_service = get_gcs_upload_service()
            image_urls: list[str] = []
            for character_id in character_ids:
                character_render = await self.repository.image.get_canonical_render(
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

            object_key = panel_render_key(
                user_id, project_id, story_id, panel_id, edit_event_id
            )
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
            await self.repository.image.create_image(image_model)
            await self.db.flush()

            # Auto-set canonical render pointer (no edit event — RENDER_PANEL records it)
            await self.repository.panel.set_canonical_render(
                panel_id, story_id, image_model.id
            )

            # TX2: complete edit event
            await self.repository.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot={"image_id": str(image_model.id)},
            )
            await self.db.commit()
            await self.db.refresh(image_model)

            # Refresh panel so canonical_render_id is up-to-date
            refreshed_panel = await self.repository.panel.get_panel(panel_id, story_id)
            if refreshed_panel is None:
                raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")
            return refreshed_panel, image_model

        except Exception:
            await self.repository.edit_event.update_edit_event(
                edit_event_id, EditEventStatus.FAILED
            )
            await self.db.commit()
            raise

    async def render_panel_edit(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        instruction: str,
        source_image_id: uuid.UUID,
        reference_image_id: uuid.UUID | None = None,
    ) -> ImageModel:
        """Edit an existing panel render via fal image-edit model.

        The source image is passed as a signed URL to fal alongside the user's
        instruction. A new Image row is created for the result; the source image
        is unchanged. The edit event records source_image_id (and reference_image_id
        if provided) for a durable audit trail.

        Side-effect note: if reference_image_id is provided it must already exist
        as a PANEL_RENDER image for this panel — upload or render it first via the
        appropriate endpoint. That image persists independently of this call.
        """
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        source_image = await self.repository.image.get_image(source_image_id)
        if source_image is None or source_image.target_id != panel_id:
            raise NotFoundError(
                f"Source image {source_image_id} not found for panel {panel_id}"
            )

        gcs_service = get_gcs_upload_service()
        source_signed_url, _ = gcs_service.generate_signed_url(source_image.object_key)

        # URL order: [source, ...character_renders, optional_reference]
        # Source anchors the edit; character renders enforce consistency;
        # optional reference acts as a style guide.
        image_urls = [source_signed_url]

        # Resolve character renders — same block as render_panel
        character_ids = await self.repository.panel.get_character_ids_for_panel(
            panel_id
        )
        character_render_ids: list[str] = []
        for character_id in character_ids:
            character_render = await self.repository.image.get_canonical_render(
                target_id=character_id,
                discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
            )
            if character_render is None:
                logger.warning(
                    f"Character {character_id} has no canonical render — "
                    f"skipping for panel {panel_id} render/edit"
                )
                continue
            signed_url, _ = gcs_service.generate_signed_url(character_render.object_key)
            image_urls.append(signed_url)
            character_render_ids.append(str(character_render.id))

        input_snapshot: dict[str, object] = {
            "source_image_id": str(source_image_id),
            "character_render_ids": character_render_ids,
        }

        if reference_image_id is not None:
            reference_image = await self.repository.image.get_image(reference_image_id)
            if reference_image is None or reference_image.target_id != panel_id:
                raise NotFoundError(
                    f"Reference image {reference_image_id} not found for panel {panel_id}"
                )
            reference_signed_url, _ = gcs_service.generate_signed_url(
                reference_image.object_key
            )
            image_urls.append(reference_signed_url)
            input_snapshot["reference_image_id"] = str(reference_image_id)

        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            operation_type=EditEventOperationType.RENDER_PANEL_EDIT,
            user_instruction=instruction,
            input_snapshot=input_snapshot,
            status=EditEventStatus.PENDING,
        )
        await self.repository.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        await self.db.commit()

        try:
            fal_response = await fal_async_client.subscribe(
                arguments={"prompt": instruction, "image_urls": image_urls},
                on_queue_update=lambda status: logger.debug(f"Fal status: {status}"),
            )
            fal_image_url = self._extract_fal_image_url(fal_response)

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

            width, height = extract_image_dimensions(image_bytes)

            object_key = panel_render_key(
                user_id, project_id, story_id, panel_id, edit_event_id
            )
            receipt = gcs_service.upload(object_key, image_bytes, content_type)

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
            await self.repository.image.create_image(image_model)
            await self.db.flush()

            # Auto-set canonical render pointer (no edit event — RENDER_PANEL_EDIT records it)
            await self.repository.panel.set_canonical_render(
                panel_id, story_id, image_model.id
            )

            await self.repository.edit_event.update_edit_event(
                edit_event_id,
                EditEventStatus.SUCCEEDED,
                output_snapshot={"image_id": str(image_model.id)},
            )
            await self.db.commit()
            await self.db.refresh(image_model)
            return image_model

        except Exception:
            await self.repository.edit_event.update_edit_event(
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
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        # Explicit cleanup of polymorphic image rows (no DB FK cascade)
        await self.repository.image.delete_images_for_target(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )

        await self.repository.panel.delete_panel(panel_id, story_id)
        await self.db.commit()

    # -----------------------------------------------------------------------
    # get_panel_renders (Story 70)
    # -----------------------------------------------------------------------

    async def get_panel_renders(
        self, project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID
    ) -> list[ImageModel]:
        """Return all render Image rows for a panel, newest first."""
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        return await self.repository.image.get_renders_for_target(
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
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")

        return await self.repository.edit_event.get_edit_events_for_target(
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            limit=limit,
        )
