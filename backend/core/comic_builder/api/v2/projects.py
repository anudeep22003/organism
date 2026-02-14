import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

from ...models import Project
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
    query = select(Project).where(Project.user_id == uuid.UUID(user_id))
    result = await db.execute(query)
    projects = result.scalars().all()
    return [ProjectListResponseSchema.model_validate(p) for p in projects]


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
