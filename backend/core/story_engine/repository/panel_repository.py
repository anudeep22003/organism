import uuid

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Panel
from ..models.panel_character import PanelCharacter
from .exception import NotFoundError


class PanelRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_panel(self, panel: Panel) -> Panel:
        self.db.add(panel)
        return panel

    async def create_panel_character(
        self, panel_id: uuid.UUID, character_id: uuid.UUID
    ) -> PanelCharacter:
        join_row = PanelCharacter(panel_id=panel_id, character_id=character_id)
        self.db.add(join_row)
        return join_row

    async def get_panel(self, panel_id: uuid.UUID, story_id: uuid.UUID) -> Panel | None:
        result = await self.db.execute(
            select(Panel).where(
                Panel.id == panel_id,
                Panel.story_id == story_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_panels_for_story(self, story_id: uuid.UUID) -> list[Panel]:
        result = await self.db.execute(
            select(Panel)
            .where(Panel.story_id == story_id)
            .order_by(asc(Panel.order_index))
        )
        return list(result.scalars().all())

    async def get_character_ids_for_panel(self, panel_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(PanelCharacter.character_id).where(
                PanelCharacter.panel_id == panel_id
            )
        )
        return list(result.scalars().all())

    async def get_panel_by_id(self, panel_id: uuid.UUID) -> Panel | None:
        """Fetch a panel by ID alone — use only when story_id is not available."""
        result = await self.db.execute(select(Panel).where(Panel.id == panel_id))
        return result.scalar_one_or_none()

    async def set_canonical_render(
        self, panel_id: uuid.UUID, story_id: uuid.UUID, image_id: uuid.UUID
    ) -> Panel:
        panel = await self.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")
        panel.canonical_render_id = image_id
        return panel

    async def delete_panel(self, panel_id: uuid.UUID, story_id: uuid.UUID) -> None:
        panel = await self.get_panel(panel_id, story_id)
        if panel is not None:
            await self.db.delete(panel)
