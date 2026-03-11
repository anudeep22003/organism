import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from ...exceptions import (
    CharacterExtractionError,
    CharacterRefinementError,
    NoStoryTextError,
    NotFoundError,
)
from ...models.edit_event import TargetType
from ...repository import Repository
from ...schemas.character import (
    CharacterRefineRequest,
    CharacterResponseSchema,
    CharacterUpdateSchema,
)
from ...schemas.edit_event import EditEventResponseSchema
from ...service import Service

router = APIRouter(tags=["characters", "v2"])


@router.post("/project/{project_id}/story/{story_id}/characters", status_code=201)
async def extract_characters_from_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[CharacterResponseSchema]:
    repository = Repository(db)
    service = Service(repository)
    try:
        characters = await service.extract_characters_from_story(project_id, story_id)
        logger.info(f"Extracted {len(characters)} characters from story {story_id}")
        return [CharacterResponseSchema.model_validate(c) for c in characters]
    except CharacterExtractionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoStoryTextError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error extracting characters: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while extracting characters",
        )


@router.get("/project/{project_id}/story/{story_id}/characters", status_code=200)
async def get_characters_for_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> list[CharacterResponseSchema]:
    repository = Repository(db)
    service = Service(repository)
    try:
        characters = await service.get_story_characters(project_id, story_id)
        return [CharacterResponseSchema.model_validate(c) for c in characters]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error getting characters for story: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while getting characters for story",
        )


@router.get(
    "/project/{project_id}/story/{story_id}/character/{character_id}", status_code=200
)
async def get_character(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> CharacterResponseSchema:
    repository = Repository(db)
    service = Service(repository)
    try:
        character = await service.get_character(project_id, story_id, character_id)
        return CharacterResponseSchema.model_validate(character)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error getting character {character_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while getting the character",
        )


@router.patch(
    "/project/{project_id}/story/{story_id}/character/{character_id}", status_code=200
)
async def update_character(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    body: CharacterUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> CharacterResponseSchema:
    repository = Repository(db)
    service = Service(repository)
    try:
        updates = body.model_dump(exclude_none=True)
        character = await service.update_character(
            project_id, story_id, character_id, updates
        )
        return CharacterResponseSchema.model_validate(character)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error updating character {character_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while updating the character",
        )


@router.post(
    "/project/{project_id}/story/{story_id}/character/{character_id}/refine",
    status_code=200,
)
async def refine_character(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    body: CharacterRefineRequest,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> CharacterResponseSchema:
    repository = Repository(db)
    service = Service(repository)
    try:
        character = await service.refine_character(
            project_id, story_id, character_id, body.instruction
        )
        return CharacterResponseSchema.model_validate(character)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except CharacterRefinementError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error refining character {character_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while refining the character",
        )


@router.delete(
    "/project/{project_id}/story/{story_id}/character/{character_id}", status_code=204
)
async def delete_character(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> None:
    repository = Repository(db)
    service = Service(repository)
    try:
        await service.delete_character(project_id, story_id, character_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error deleting character {character_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while deleting the character",
        )


# add a history endpoint
@router.get("/project/{project_id}/story/{story_id}/character/{character_id}/history")
async def get_character_history(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    limit: int = 20,
) -> list[EditEventResponseSchema]:
    repository = Repository(db)
    events = await repository.get_edit_events_for_target(
        TargetType.CHARACTER, character_id, limit=limit
    )
    return [EditEventResponseSchema.model_validate(e) for e in events]
