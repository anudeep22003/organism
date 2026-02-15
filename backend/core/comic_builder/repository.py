import uuid
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Project, Story


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
                selectinload(Project.stories).selectinload(Story.characters),
                selectinload(Project.stories).selectinload(Story.panels),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
