import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .exceptions import ProjectNotFoundError
from .models import Project
from .state import ConsolidatedComicState


class ProjectStateManager:
    """Manages project state operations: fetch, validate, and sync."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def fetch_project(self, project_id: uuid.UUID) -> Project:
        """Fetch project from database by ID."""
        result = await self._db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return project

    def get_validated_state(self, project: Project) -> ConsolidatedComicState:
        """Validate project has state and return parsed ConsolidatedComicState."""
        if not project.state:
            raise ValueError(f"Project {project.id} state unexpectedly not initialized")
        return ConsolidatedComicState.model_validate(project.state)

    async def sync_state(self, project: Project, state: ConsolidatedComicState) -> None:
        """Persist state back to project and commit."""
        project.state = state.model_dump()
        await self._db.commit()
