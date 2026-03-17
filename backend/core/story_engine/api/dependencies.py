import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

from ..models import Project
from ..service import Service


async def verify_project_access(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> uuid.UUID:
    # Verify that the user has access to the project.
    # Raise an error if the user does not have access.
    query = select(Project).where(Project.id == project_id)
    result = await db.execute(query)
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.user_id != uuid.UUID(user_id):
        raise HTTPException(
            status_code=403, detail="User does not have access to project"
        )

    return project.id


async def get_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> Service:
    return Service(db_session=db)
