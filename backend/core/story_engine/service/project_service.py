import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NotFoundError
from ..models import Project, Story
from ..repository import Repository
from ..repository.exception import NotFoundError as RepoNotFoundError
from .story_identity_service import generate_story_identity


class ProjectService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repository = Repository(db_session)

    async def get_all_projects_of_user(
        self, user_id: uuid.UUID
    ) -> list[tuple[Project, int]]:
        return await self.repository.project.get_all_projects_of_user_with_story_count(
            user_id
        )

    async def create_project(
        self, user_id: uuid.UUID, name: str | None = None
    ) -> Project:
        project = await self.repository.project.create_project(
            user_id=user_id, name=name
        )
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def delete_project(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Hard-delete a project. Raises NotFoundError if not found or not owned."""
        try:
            await self.repository.project.delete_project(project_id, user_id)
        except RepoNotFoundError as e:
            raise NotFoundError(str(e)) from e
        await self.db.commit()

    async def rename_project(
        self, project_id: uuid.UUID, user_id: uuid.UUID, name: str
    ) -> Project:
        """Rename a project. Raises NotFoundError if not found or not owned."""
        try:
            project = await self.repository.project.rename_project(
                project_id, user_id, name
            )
        except RepoNotFoundError as e:
            raise NotFoundError(str(e)) from e
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_project_details(
        self, user_id: uuid.UUID, project_id: uuid.UUID
    ) -> Project | None:
        return await self.repository.project.get_project_details(user_id, project_id)

    async def get_or_create_default_project(self, user_id: uuid.UUID) -> Project:
        """Return the user's default project, creating one if none exists.

        Always returns a Project with stories eager-loaded.
        """
        project = await self.repository.project.get_default_project_of_user(user_id)
        if project is not None:
            return project
        await self.repository.project.create_project(user_id, name=None)
        await self.db.commit()
        project = await self.repository.project.get_default_project_of_user(user_id)
        assert project is not None  # guaranteed — we just created it
        return project

    async def create_story(
        self,
        project_id: uuid.UUID,
        meta: dict | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Story:
        story = await self.repository.story.create_new_story(
            project_id, meta=meta or {}, name=name, description=description
        )
        await self.db.commit()
        await self.db.refresh(story)

        if meta and not (story.name and story.description):
            identity = await generate_story_identity(meta)
            if identity:
                if not story.name:
                    story.name = identity[0]
                if not story.description:
                    story.description = identity[1]
                await self.db.commit()
                await self.db.refresh(story)

        return story

    async def delete_story(self, project_id: uuid.UUID, story_id: uuid.UUID) -> None:
        try:
            await self.repository.story.delete_story(project_id, story_id)
        except RepoNotFoundError as e:
            raise NotFoundError(str(e)) from e
        await self.db.commit()
