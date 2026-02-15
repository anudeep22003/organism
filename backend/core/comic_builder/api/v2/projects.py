import uuid
from typing import Annotated, Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

from ...models import Project, Story
from ...schemas import (
    ProjectCreateSchema,
    ProjectListResponseSchema,
    ProjectResponseSchema,
)

router = APIRouter(tags=["comic", "builder", "v2", "projects"])


@router.get("/projects")
async def get_all_projects_of_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[ProjectListResponseSchema]:
    query = (
        select(Project, func.count(Story.id).label("story_count"))
        .outerjoin(Story, Story.project_id == Project.id)
        .where(Project.user_id == uuid.UUID(user_id))
        .group_by(Project.id)
    )
    result = await db.execute(query)
    rows: Sequence[tuple[Project, int]] = result.tuples().all()
    return [
        ProjectListResponseSchema(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
            story_count=story_count,
        )
        for (project, story_count) in rows
    ]


@router.post("/projects")
async def create_project(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    project_data: ProjectCreateSchema,
) -> ProjectResponseSchema:
    project = Project(user_id=uuid.UUID(user_id), name=project_data.name)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponseSchema.model_validate(project)
