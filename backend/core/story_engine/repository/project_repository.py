import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Project, Story
from .exception import NotFoundError


class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_projects_of_user_with_story_count(
        self, user_id: uuid.UUID
    ) -> list[tuple[Project, int]]:
        query = (
            select(Project, func.count(Story.id).label("story_count"))
            .outerjoin(Story, Story.project_id == Project.id)
            .where(Project.user_id == user_id)
            .group_by(Project.id)
        )
        result = await self.db.execute(query)
        projects = result.tuples().all()
        return list(projects)

    async def create_project(
        self, user_id: uuid.UUID, name: str | None = None
    ) -> Project:
        project = Project(user_id=user_id, name=name)
        self.db.add(project)
        return project

    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a project and all its children (stories → characters, panels, images).

        Raises NotFoundError if the project does not exist or does not belong
        to the given user.
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        await self.db.delete(project)

    async def rename_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, name: str
    ) -> Project:
        """Update project.name and return the updated Project.

        Raises NotFoundError if the project does not exist or does not belong
        to the given user.
        """
        result = await self.db.execute(
            select(Project).where(Project.id == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NotFoundError(f"Project {project_id} not found")
        project.name = name
        return project

    async def get_project_details(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> Project | None:
        query = (
            select(Project)
            .where(Project.id == project_id, Project.user_id == user_id)
            .options(
                selectinload(Project.stories),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_default_project_of_user(self, user_id: uuid.UUID) -> Project | None:
        """Return the user's oldest project with stories eager-loaded, or None."""
        query = (
            select(Project)
            .where(Project.user_id == user_id)
            .options(selectinload(Project.stories))
            .order_by(Project.created_at.asc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
