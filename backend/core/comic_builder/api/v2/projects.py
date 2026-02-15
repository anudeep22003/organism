import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

from ...repository import Repository
from ...schemas import (
    ProjectCreateSchema,
    ProjectListResponseSchema,
    ProjectRelationalStateSchema,
    ProjectResponseSchema,
)

router = APIRouter(tags=["comic", "builder", "v2", "projects"])


@router.get("/projects")
async def get_all_projects_of_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[ProjectListResponseSchema]:
    repository = Repository(db)
    rows = await repository.get_all_projects_of_user_with_story_count(user_id)
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
    repository = Repository(db)
    project = await repository.create_project(user_id, project_data.name)
    return ProjectResponseSchema.model_validate(project)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ProjectRelationalStateSchema:
    repository = Repository(db)
    project = await repository.get_project_details(user_id, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return ProjectRelationalStateSchema.model_validate(project)
