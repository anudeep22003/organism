import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Character, EditEvent, Project, Story
from ..models.edit_event import EditEventStatus, OperationType
from .repository_v2 import RepositoryV2


class RepositoryOld:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository_v2 = RepositoryV2(db)

    async def get_all_projects_of_user_with_story_count(
        self, user_id: str
    ) -> list[tuple[Project, int]]:
        return (
            await self.repository_v2.project.get_all_projects_of_user_with_story_count(
                user_id
            )
        )

    async def create_project(self, user_id: str, name: str | None = None) -> Project:
        project = await self.repository_v2.project.create_project(
            user_id=user_id, name=name
        )
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project_details(
        self, user_id: str, project_id: uuid.UUID
    ) -> Project | None:
        return await self.repository_v2.project.get_project_details(
            user_id=user_id,
            project_id=project_id,
        )

    async def create_new_story(self, project_id: uuid.UUID) -> Story:
        story = await self.repository_v2.story.create_new_story(project_id)
        await self.db.commit()
        await self.db.refresh(story)
        return story

    async def get_story(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> Story | None:
        return await self.repository_v2.story.get_story(project_id, story_id)

    async def delete_story(self, project_id: uuid.UUID, story_id: uuid.UUID) -> None:
        await self.repository_v2.story.delete_story(project_id, story_id)
        await self.db.commit()

    async def get_story_with_project(self, story_id: uuid.UUID) -> Story | None:
        return await self.repository_v2.story.get_story_with_project(story_id)

    async def update_story_with_story_text_and_user_input_text(
        self,
        story_id: uuid.UUID,
        story_text: str,
        user_input_text: str,
        source_event_id: uuid.UUID | None = None,
    ) -> Story:
        story = await self.repository_v2.story.update_story_with_story_text_and_user_input_text(
            story_id=story_id,
            story_text=story_text,
            user_input_text=user_input_text,
            source_event_id=source_event_id,
        )
        await self.db.commit()
        await self.db.refresh(story)
        return story

    # ── Edit Event methods ──────────────────────────────────────

    async def create_edit_event(
        self,
        project_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        operation_type: OperationType,
        user_instruction: str,
        input_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = await self.repository_v2.edit_event.create_edit_event(
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            operation_type=operation_type,
            user_instruction=user_instruction,
            input_snapshot=input_snapshot,
        )
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def complete_edit_event(
        self,
        edit_event_id: uuid.UUID,
        status: EditEventStatus,
        output_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = await self.repository_v2.edit_event.update_edit_event(
            edit_event_id, status, output_snapshot
        )
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_edit_events_for_target(
        self, target_type: str, target_id: uuid.UUID, limit: int = 20
    ) -> list[EditEvent]:
        return await self.repository_v2.edit_event.get_edit_events_for_target(
            target_type=target_type,
            target_id=target_id,
            limit=limit,
        )

    async def bulk_create_characters(self, characters: list[Character]) -> None:
        await self.repository_v2.character.bulk_create_characters(characters)
        await self.db.commit()

    async def get_all_characters_for_a_story(
        self, story_id: uuid.UUID
    ) -> list[Character]:
        return await self.repository_v2.character.get_all_characters_for_a_story(
            story_id
        )

    async def get_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID
    ) -> Character | None:
        return await self.repository_v2.character.get_character(character_id, story_id)

    async def get_character_for_user_in_project_and_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> Character | None:
        return await self.repository_v2.character.get_character_for_user_in_project_and_story(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
        )

    async def update_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID, updates: dict[str, Any]
    ) -> Character:
        character = await self.repository_v2.character.update_character(
            character_id=character_id,
            story_id=story_id,
            updates=updates,
        )
        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def replace_character_attributes(
        self,
        character_id: uuid.UUID,
        story_id: uuid.UUID,
        attributes: dict[str, Any],
        source_event_id: uuid.UUID | None = None,
    ) -> Character:
        character = await self.repository_v2.character.replace_character_attributes(
            character_id=character_id,
            story_id=story_id,
            attributes=attributes,
            source_event_id=source_event_id,
        )

        await self.db.commit()
        await self.db.refresh(character)
        return character

    async def delete_character(
        self, character_id: uuid.UUID, story_id: uuid.UUID
    ) -> None:
        await self.repository_v2.character.delete_character(character_id, story_id)
        await self.db.commit()

    async def update_character_render_url(
        self, character_id: uuid.UUID, story_id: uuid.UUID, render_url: str
    ) -> Character:
        character = await self.repository_v2.character.update_character_render_url(
            character_id=character_id,
            story_id=story_id,
            render_url=render_url,
        )
        await self.db.commit()
        await self.db.refresh(character)
        return character
