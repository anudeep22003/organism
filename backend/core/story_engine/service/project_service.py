import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Project, Story
from ..repository import Repository, RepositoryV2


class ProjectService:
    def __init__(
        self,
        db_session: AsyncSession,
        repository: Repository | None = None,
    ):
        self.repository = repository or Repository(db_session)
        self.repository_v2 = RepositoryV2(db_session)

    async def get_all_projects_of_user(self, user_id: str) -> list[tuple[Project, int]]:
        return (
            await self.repository_v2.project.get_all_projects_of_user_with_story_count(
                user_id
            )
        )

    async def create_project(self, user_id: str, name: str | None = None) -> Project:
        return await self.repository.create_project(user_id, name)

    async def get_project_details(
        self, user_id: str, project_id: uuid.UUID
    ) -> Project | None:
        return await self.repository_v2.project.get_project_details(user_id, project_id)

    async def create_story(self, project_id: uuid.UUID) -> Story:
        return await self.repository.create_new_story(project_id)

    async def delete_story(self, project_id: uuid.UUID, story_id: uuid.UUID) -> None:
        await self.repository.delete_story(project_id, story_id)
