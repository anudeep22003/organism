import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.comic_builder.models import Project
from core.comic_builder.schemas import (
    ProjectCreateSchema,
    ProjectResponseSchema,
    ProjectUpdateSchema,
)
from core.services.database import get_async_db_session

router = APIRouter(tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/projects")
async def list_projects(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[ProjectResponseSchema]:
    query = select(Project).where(Project.user_id == uuid.UUID(user_id))
    result = await db.execute(query)
    projects = result.scalars().all()
    return [ProjectResponseSchema.model_validate(p) for p in projects]


@router.post("/projects", status_code=status.HTTP_201_CREATED)
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


@router.get("/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ProjectResponseSchema:
    query = select(Project).where(
        Project.id == project_id, Project.user_id == uuid.UUID(user_id)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return ProjectResponseSchema.model_validate(project)


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    update_data: ProjectUpdateSchema,
) -> ProjectResponseSchema:
    query = select(Project).where(
        Project.id == project_id, Project.user_id == uuid.UUID(user_id)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return ProjectResponseSchema.model_validate(project)


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> None:
    query = select(Project).where(
        Project.id == project_id, Project.user_id == uuid.UUID(user_id)
    )
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    await db.delete(project)
    await db.commit()
