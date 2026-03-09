import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from ...exceptions import CharacterExtractionError, NoStoryTextError, NotFoundError
from ...repository import Repository
from ...schemas.character import CharacterResponseSchema
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
