import uuid
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from core.auth import (
    get_current_user_id,
)
from core.services.database import (
    get_async_db_session,
)

from ...events import EventEnvelope
from ...exceptions import InvalidUserIDError, NotFoundError, NotOwnedError
from ...repository import Repository
from ...schemas.story import (
    GenerateStoryRequest,
    StoryResponseSchema,
)
from ...service import Service

router = APIRouter(tags=["story"])


@router.get("/project/{project_id}/story/{story_id}")
async def get_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> StoryResponseSchema:
    repository = Repository(db)
    story = await repository.get_story(project_id, story_id)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found in project"
        )
    return StoryResponseSchema.model_validate(story)


async def _as_ndjson(stream: AsyncIterator[EventEnvelope]) -> AsyncIterator[str]:
    async for event in stream:
        yield event.model_dump_json() + "\n"


@router.post("/story/{story_id}/generate")
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
) -> StreamingResponse:
    repository = Repository(db)
    service = Service(repository)
    try:
        stream = await service.generate_story(user_id, story_id, request)
        return StreamingResponse(
            content=_as_ndjson(stream),
            media_type="application/x-ndjson",
        )
    except (InvalidUserIDError, NotFoundError, NotOwnedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
