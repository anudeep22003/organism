import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from ..models import Story
from .exception import NotFoundError


class StoryRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_new_story(
        self,
        project_id: uuid.UUID,
        meta: dict | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Story:
        story = Story(
            project_id=project_id, meta=meta or {}, name=name, description=description
        )
        self.db.add(story)
        return story

    async def get_story(
        self, project_id: uuid.UUID, story_id: uuid.UUID
    ) -> Story | None:
        stmt = select(Story).where(Story.id == story_id, Story.project_id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_story(self, project_id: uuid.UUID, story_id: uuid.UUID) -> None:
        story = await self.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found in project {project_id}")
        await self.db.delete(story)

    async def get_story_with_project(self, story_id: uuid.UUID) -> Story | None:
        stmt = (
            select(Story).where(Story.id == story_id).options(joinedload(Story.project))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_story_meta_and_identity(
        self,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        meta: dict | None,
        name: str | None,
        description: str | None,
    ) -> Story:
        """Update meta, name, and/or description on a story.

        Only fields that are not None are written — omitted fields are untouched.
        Raises NotFoundError if the story does not exist in the given project.
        """
        story = await self.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found in project {project_id}")
        if meta is not None:
            story.meta = meta
        if name is not None:
            story.name = name
        if description is not None:
            story.description = description
        return story

    async def update_story_with_story_text_and_user_input_text(
        self,
        story_id: uuid.UUID,
        story_text: str,
        user_input_text: str,
        source_event_id: uuid.UUID | None = None,
    ) -> Story:
        story = await self.db.get(Story, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found")

        story.story_text = story_text
        story.user_input_text = user_input_text
        if source_event_id is not None:
            story.source_event_id = source_event_id
        return story
