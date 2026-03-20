import uuid
from typing import Any

from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Character, Project, Story
from .exception import NotFoundError


class CharacterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create_characters(self, characters: list[Character]) -> None:
        self.db.add_all(characters)

    async def get_all_characters_for_a_story(
        self, story_id: uuid.UUID
    ) -> list[Character]:
        stmt = select(Character).where(Character.story_id == story_id)
        result = await self.db.execute(stmt)
        characters = result.scalars().all()
        return list(characters)

    async def get_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID
    ) -> Character | None:
        stmt = select(Character).where(
            Character.id == character_id, Character.story_id == story_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_character_for_user_in_project_and_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> Character | None:
        stmt = (
            select(Character)
            .join(Story)
            .join(Project)
            .where(
                Character.id == character_id,
                Story.id == story_id,
                Project.id == project_id,
                Project.user_id == uuid.UUID(user_id),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID, updates: dict[str, Any]
    ) -> Character:
        character = await self.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        meta = updates.pop("meta", None)
        attribute_updates = {k: v for k, v in updates.items() if v is not None}
        if attribute_updates:
            character.attributes = {**character.attributes, **attribute_updates}
            if "name" in attribute_updates:
                character.name = attribute_updates["name"]

        if meta is not None:
            character.meta = {**character.meta, **meta}
        return character

    async def replace_character_attributes(
        self,
        character_id: uuid.UUID,
        story_id: uuid.UUID,
        attributes: dict[str, Any],
        source_event_id: uuid.UUID | None = None,
    ) -> Character:
        character = await self.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )

        character.attributes = attributes
        character.name = attributes["name"]
        character.slug = slugify(attributes["name"])
        if source_event_id is not None:
            character.source_event_id = source_event_id
        return character

    async def delete_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID
    ) -> None:
        character = await self.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )
        await self.db.delete(character)

    async def update_character_render_url(
        self, character_id: uuid.UUID, story_id: uuid.UUID, render_url: str
    ) -> Character:
        character = await self.get_character(character_id, story_id)
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in story {story_id}"
            )
        character.render_url = render_url
        return character
