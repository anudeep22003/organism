import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth.api import get_current_user_id

from ...exceptions import NotFoundError
from ...schemas import (
    ProjectCreateSchema,
    ProjectListResponseSchema,
    ProjectRelationalStateSchema,
    ProjectRenameSchema,
    ProjectResponseSchema,
    StoryCreateSchema,
    StoryResponseSchema,
)
from ...service import ProjectService
from ..dependencies import get_project_service

router = APIRouter(tags=["comic", "builder", "v2", "projects"])


@router.get("/projects")
async def get_all_projects_of_user(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> list[ProjectListResponseSchema]:
    projects = await service.get_all_projects_of_user(user_id)
    return [
        ProjectListResponseSchema(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            updated_at=project.updated_at,
            story_count=story_count,
        )
        for (project, story_count) in projects
    ]


@router.post("/projects")
async def create_project(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    project_data: ProjectCreateSchema,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponseSchema:
    project = await service.create_project(user_id, project_data.name)
    return ProjectResponseSchema.model_validate(project)


@router.get("/projects/me")
async def get_my_project(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRelationalStateSchema:
    """Return the user's default project, creating one if none exists.

    Idempotent — safe to call on every login. Never returns 404.
    """
    project = await service.get_or_create_default_project(user_id)
    return ProjectRelationalStateSchema.model_validate(project)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRelationalStateSchema:
    project = await service.get_project_details(user_id, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return ProjectRelationalStateSchema.model_validate(project)


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Hard-delete a project and all its children (cascade in DB)."""
    try:
        await service.delete_project(project_id, user_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )


@router.patch("/projects/{project_id}", status_code=200)
async def rename_project(
    project_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    body: ProjectRenameSchema,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponseSchema:
    """Rename a project. Only `name` is mutable in v2."""
    try:
        project = await service.rename_project(project_id, user_id, body.name)
        return ProjectResponseSchema.model_validate(project)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )


@router.post("/projects/{project_id}/story")
async def create_story(
    project_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    story_data: StoryCreateSchema,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> StoryResponseSchema:
    story = await service.create_story(
        project_id,
        meta=story_data.meta,
        name=story_data.name,
        description=story_data.description,
    )
    return StoryResponseSchema.model_validate(story)


@router.delete("/projects/{project_id}/story/{story_id}", status_code=204)
async def delete_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    try:
        await service.delete_story(project_id, story_id)
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found in project"
        )
