import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from core.auth import (
    get_current_user_id,
)
from core.services.database import (
    get_async_db_session,
)

from ...exceptions import InvalidUserIDError, NotFoundError, NotOwnedError
from ...repository import Repository
from ...schemas.story import (
    GenerateStoryRequest,
)
from ...service import Service

router = APIRouter(prefix="/story", tags=["story"])


@router.post("/{story_id}/generate")
async def generate_story(
    user_id: Annotated[
        str,
        Depends(get_current_user_id),
    ],
    story_id: uuid.UUID,
    db: Annotated[
        AsyncSession,
        Depends(get_async_db_session),
    ],
    request: GenerateStoryRequest,
) -> None:
    repository = Repository(db)
    service = Service(repository)
    try:
        await service.generate_story(user_id, story_id, request)
    except (InvalidUserIDError, NotFoundError, NotOwnedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None
