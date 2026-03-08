import uuid
from typing import Any, Sequence

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from .models import EditEvent, Project, Story


class NotFoundError(Exception):
    """Base class for not found errors."""

    pass


class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_projects_of_user_with_story_count(
        self, user_id: str
    ) -> Sequence[tuple[Project, int]]:
        query = (
            select(Project, func.count(Story.id).label("story_count"))
            .outerjoin(Story, Story.project_id == Project.id)
            .where(Project.user_id == uuid.UUID(user_id))
            .group_by(Project.id)
        )
        result = await self.db.execute(query)
        return result.tuples().all()

    async def create_project(self, user_id: str, name: str | None = None) -> Project:
        project = Project(user_id=uuid.UUID(user_id), name=name)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project_details(
        self, user_id: str, project_id: uuid.UUID
    ) -> Project | None:
        query = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == uuid.UUID(user_id))
            .options(
                selectinload(Project.stories),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_new_story(self, project_id: uuid.UUID) -> Story:
        story = Story(project_id=project_id)
        self.db.add(story)
        await self.db.commit()
        await self.db.refresh(story)
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
        await self.db.commit()

    async def get_story_with_project(self, story_id: uuid.UUID) -> Story | None:
        stmt = (
            select(Story).where(Story.id == story_id).options(joinedload(Story.project))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

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
        await self.db.commit()
        await self.db.refresh(story)
        return story

    # ── Edit Event methods ──────────────────────────────────────

    async def create_edit_event(
        self,
        project_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        operation_type: str,
        user_instruction: str,
        input_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = EditEvent(
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            operation_type=operation_type,
            user_instruction=user_instruction,
            input_snapshot=input_snapshot,
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def complete_edit_event(
        self,
        event_id: uuid.UUID,
        status: str,
        output_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = await self.db.get(EditEvent, event_id)
        if event is None:
            raise NotFoundError(f"EditEvent {event_id} not found")

        event.status = status
        if output_snapshot is not None:
            event.output_snapshot = output_snapshot
        await self.db.commit()
        await self.db.refresh(event)
        return event

    async def get_edit_events_for_target(
        self, target_type: str, target_id: uuid.UUID, limit: int = 20
    ) -> Sequence[EditEvent]:
        stmt = (
            select(EditEvent)
            .where(
                EditEvent.target_type == target_type,
                EditEvent.target_id == target_id,
            )
            .order_by(desc(EditEvent.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
