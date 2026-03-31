"""
PanelService — business logic for the panel pipeline.

Currently implements:
  - generate_panels: bulk generate all panels for a story from story text
"""

import textwrap
import uuid
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.intelligence import instructor_client

from ..exceptions import NoStoryTextError, NotFoundError
from ..models import EditEvent, Panel
from ..models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from ..models.image import ImageDiscriminatorKey
from ..repository import RepositoryV2
from ..schemas.panel import GeneratedPanelsResponse, PanelContent


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

        # Call LLM to get structured panel content
        generated = await self._extract_panels_from_story(story_text)

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
                )
            else:
                panel_content = await self._regenerate_panel(
                    existing_attributes=input_attrs,
                    instruction=instruction or "Regenerate this panel.",
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
        self, story_text: str, order_index: int
    ) -> PanelContent:
        """LLM call for first-time single panel generation."""
        prompt = textwrap.dedent(f"""
            You are a comic book artist. Generate a single comic panel for panel #{order_index + 1}.

            Story:
            {story_text}

            Return a single panel with background description, dialogue, and character slugs.
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=PanelContent,
            messages=[
                {
                    "role": "system",
                    "content": "Generate a single comic panel from story context.",
                },
                {"role": "user", "content": prompt},
            ],
        )

    async def _regenerate_panel(
        self, existing_attributes: dict[str, Any], instruction: str
    ) -> PanelContent:
        """LLM call for panel regeneration using existing attributes and instruction."""
        import json

        prompt = textwrap.dedent(f"""
            You are a comic book artist. Refine this panel based on the instruction.

            Current panel:
            {json.dumps(existing_attributes, indent=2)}

            Instruction: {instruction}

            Return the updated panel.
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=PanelContent,
            messages=[
                {
                    "role": "system",
                    "content": "Refine a comic panel based on an instruction.",
                },
                {"role": "user", "content": prompt},
            ],
        )

    async def _extract_panels_from_story(
        self, story_text: str
    ) -> GeneratedPanelsResponse:
        """Call instructor to extract structured panel content from story text."""
        prompt = textwrap.dedent(f"""
            You are a comic book artist and writer.
            Extract a list of comic book panels from the following story.
            For each panel provide:
              - background: a brief visual description of the setting/scene
              - dialogue: key spoken or thought dialogue in the panel (empty string if none)
              - characters: list of character slugs (lowercase-hyphenated names) who appear

            Story:
            {story_text}
        """).strip()

        return await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=GeneratedPanelsResponse,
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
    # get_panel_history (for Story 80)
    # -----------------------------------------------------------------------

    async def get_panel_history(
        self, panel_id: uuid.UUID, limit: int = 20
    ) -> list[EditEvent]:
        """Return all edit events for a panel, ordered newest first."""
        return await self.repository_v2.edit_event.get_edit_events_for_target(
            target_type=EditEventTargetType.PANEL,
            target_id=panel_id,
            limit=limit,
        )
