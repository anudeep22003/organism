import uuid
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from core.auth.dependencies import get_current_user_id

from ...events import EventEnvelope
from ...exceptions import InvalidUserIDError, NotFoundError, NotOwnedError
from ...schemas.edit_event import EditEventResponseSchema
from ...schemas.story import (
    GenerateStoryRequest,
    StoryResponseSchema,
    StoryUpdateSchema,
)
from ...service import StoryService
from ..dependencies import get_story_service

router = APIRouter(tags=["story"])


@router.get("/project/{project_id}/story/{story_id}")
async def get_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[StoryService, Depends(get_story_service)],
) -> StoryResponseSchema:
    story = await service.get_story(project_id, story_id)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found in project"
        )
    return StoryResponseSchema.model_validate(story)


async def _as_ndjson(stream: AsyncIterator[EventEnvelope]) -> AsyncIterator[str]:
    async for event in stream:
        yield event.model_dump_json() + "\n"


@router.post("/project/{project_id}/story/{story_id}/generate")
async def generate_story(
    user_id: Annotated[
        uuid.UUID,
        Depends(get_current_user_id),
    ],
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    request: GenerateStoryRequest,
    service: Annotated[StoryService, Depends(get_story_service)],
) -> StreamingResponse:
    try:
        stream = await service.generate_story(user_id, project_id, story_id, request)
        return StreamingResponse(
            content=_as_ndjson(stream),
            media_type="application/x-ndjson",
        )
    except (InvalidUserIDError, NotFoundError, NotOwnedError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/project/{project_id}/story/{story_id}")
async def update_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    body: StoryUpdateSchema,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[StoryService, Depends(get_story_service)],
) -> StoryResponseSchema:
    """Partially update a story's meta, name, and/or description.

    Only fields present in the request body are written — omitted fields are untouched.
    """
    try:
        story = await service.update_story(
            project_id,
            story_id,
            meta=body.meta,
            name=body.name,
            description=body.description,
        )
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Story not found in project"
        )
    return StoryResponseSchema.model_validate(story)


@router.get("/project/{project_id}/story/{story_id}/history")
async def get_story_history(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[StoryService, Depends(get_story_service)],
    limit: int = 20,
) -> list[EditEventResponseSchema]:
    events = await service.get_story_history(story_id, limit=limit)
    return [EditEventResponseSchema.model_validate(e) for e in events]
