import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from core.auth import get_current_user_id

from ...exceptions import (
    CharacterExtractionError,
    CharacterRefinementError,
    NoStoryTextError,
    NotFoundError,
    UploadImageError,
)
from ...schemas.character import (
    CharacterRefineRequest,
    CharacterResponseSchema,
    CharacterUpdateSchema,
)
from ...schemas.edit_event import EditEventResponseSchema
from ...schemas.image import ImageResponseSchema
from ...service import CharacterService
from ..dependencies import get_character_service

router = APIRouter(tags=["characters", "v2"])


@router.post("/project/{project_id}/story/{story_id}/characters", status_code=201)
async def extract_characters_from_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> list[CharacterResponseSchema]:
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
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> list[CharacterResponseSchema]:
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
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterResponseSchema:
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
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterResponseSchema:
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
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterResponseSchema:
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
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> None:
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


@router.get("/project/{project_id}/story/{story_id}/character/{character_id}/history")
async def get_character_history(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
    limit: int = 20,
) -> list[EditEventResponseSchema]:
    events = await service.get_character_history(character_id, limit=limit)
    return [EditEventResponseSchema.model_validate(e) for e in events]


@router.post("/project/{project_id}/story/{story_id}/character/{character_id}/render")
async def render_character(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterResponseSchema:
    character = await service.render_character(project_id, story_id, character_id)
    return CharacterResponseSchema.model_validate(character)


@router.post(
    "/project/{project_id}/story/{story_id}/character/{character_id}/upload-reference-image",
    status_code=status.HTTP_201_CREATED,
)
async def upload_reference_image(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    image: UploadFile = File(...),
) -> ImageResponseSchema:
    try:
        image_model = await service.upload_reference_image(
            user_id, project_id, story_id, character_id, image
        )
        return ImageResponseSchema.model_validate(image_model)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UploadImageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error uploading reference image for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the reference image",
        )
