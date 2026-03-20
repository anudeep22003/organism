import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Project, Story
from ..repository import RepositoryV2


class ProjectService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repository_v2 = RepositoryV2(db_session)

    async def get_all_projects_of_user(self, user_id: str) -> list[tuple[Project, int]]:
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
        return await self.repository_v2.project.get_project_details(user_id, project_id)

    async def create_story(self, project_id: uuid.UUID) -> Story:
        story = await self.repository_v2.story.create_new_story(project_id)
        await self.db.commit()
        await self.db.refresh(story)
        return story

    async def delete_story(self, project_id: uuid.UUID, story_id: uuid.UUID) -> None:
        await self.repository_v2.story.delete_story(project_id, story_id)
        await self.db.commit()
