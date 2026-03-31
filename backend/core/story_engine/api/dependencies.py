import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

from ..models import Project
from ..repository import RepositoryV2
from ..service import (
    CharacterService,
    ImageService,
    PanelService,
    ProjectService,
    StoryService,
)


async def verify_project_access(
    project_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> uuid.UUID:
    # Verify that the user has access to the project.
    # Raise an error if the user does not have access.
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != user_id:
        raise HTTPException(
            status_code=403, detail="User does not have access to project"
        )

    return project.id


async def get_project_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ProjectService:
    return ProjectService(db_session=db)


async def get_story_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> StoryService:
    return StoryService(db_session=db)


async def get_character_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> CharacterService:
    return CharacterService(db_session=db)


async def get_image_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ImageService:
    return ImageService(db=db, repository_v2=RepositoryV2(db))


async def get_panel_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> PanelService:
    return PanelService(db_session=db)
