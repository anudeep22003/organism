import uuid
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from core.auth.api import get_current_user_id

from ...exceptions import (
    CharacterExtractionError,
    CharacterRefinementError,
    NoStoryTextError,
    NotFoundError,
    UploadImageError,
)
from ...schemas.character import (
    CharacterRefineRequest,
    CharacterRenderEditRequest,
    CharacterRenderReferencesSchema,
    CharacterResponseSchema,
    CharacterUpdateSchema,
    SetCanonicalRenderRequest,
)
from ...schemas.edit_event import EditEventResponseSchema
from ...schemas.image import ImageResponseSchema
from ...service import CharacterService, ImageService
from ..dependencies import get_character_service, get_image_service

router = APIRouter(tags=["characters", "v2"])


def _build_character_full(
    character: object,
    image: object | None,
    reference_images: Sequence[object] | None = None,
) -> CharacterRenderReferencesSchema:
    """Assemble a CharacterRenderReferencesSchema from ORM objects (per Decision 12)."""
    return CharacterRenderReferencesSchema(
        character=CharacterResponseSchema.model_validate(character),
        canonical_render=ImageResponseSchema.model_validate(image) if image else None,
        reference_images=[
            ImageResponseSchema.model_validate(r) for r in (reference_images or [])
        ],
    )


@router.post("/project/{project_id}/story/{story_id}/characters", status_code=201)
async def extract_characters_from_story(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> list[CharacterRenderReferencesSchema]:
    try:
        characters = await service.extract_characters_from_story(project_id, story_id)
        logger.info(f"Extracted {len(characters)} characters from story {story_id}")
        # Newly extracted characters have no renders or reference images yet
        return [_build_character_full(c, None) for c in characters]
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> list[CharacterRenderReferencesSchema]:
    try:
        characters = await service.get_story_characters(project_id, story_id)
        result = []
        for character in characters:
            render = await service.get_canonical_character_render(character.id)
            refs = await service.get_character_reference_images(character.id)
            result.append(_build_character_full(character, render, refs))
        return result
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
) -> CharacterRenderReferencesSchema:
    try:
        character = await service.get_character(project_id, story_id, character_id)
        render = await service.get_canonical_character_render(character.id)
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, render, refs)
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
) -> CharacterRenderReferencesSchema:
    try:
        updates = body.model_dump(exclude_none=True)
        character = await service.update_character(
            project_id, story_id, character_id, updates
        )
        render = await service.get_canonical_character_render(character.id)
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, render, refs)
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
) -> CharacterRenderReferencesSchema:
    try:
        character = await service.refine_character(
            project_id, story_id, character_id, body.instruction
        )
        render = await service.get_canonical_character_render(character.id)
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, render, refs)
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
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
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRenderReferencesSchema:
    try:
        character, image = await service.render_character(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
        )
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, image, refs)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error rendering character {character_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while rendering the character",
        )


@router.post(
    "/project/{project_id}/story/{story_id}/character/{character_id}/upload-reference-image",
    status_code=status.HTTP_201_CREATED,
)
async def upload_reference_image(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    service: Annotated[CharacterService, Depends(get_character_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    image: UploadFile = File(...),
) -> CharacterRenderReferencesSchema:
    try:
        await service.upload_reference_image(
            user_id, project_id, story_id, character_id, image
        )
        character = await service.get_character(project_id, story_id, character_id)
        render = await service.get_canonical_character_render(character.id)
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, render, refs)
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


@router.get(
    "/project/{project_id}/story/{story_id}/character/{character_id}/renders",
    status_code=200,
)
async def get_character_renders(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> list[ImageResponseSchema]:
    """Return all render variations for a character, ordered newest first.

    Returns an empty list (not 404) when the character exists but has no renders.
    """
    try:
        images = await service.get_character_renders(project_id, story_id, character_id)
        return [ImageResponseSchema.model_validate(img) for img in images]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching renders for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching character renders",
        )


@router.get(
    "/project/{project_id}/story/{story_id}/character/{character_id}/reference-images",
    status_code=200,
)
async def get_character_reference_images(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ImageService, Depends(get_image_service)],
) -> list[ImageResponseSchema]:
    try:
        images = await service.get_character_reference_images(
            user_id, project_id, story_id, character_id
        )
        return [ImageResponseSchema.model_validate(image) for image in images]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error fetching reference images for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching reference images",
        )


@router.delete(
    "/project/{project_id}/story/{story_id}/character/{character_id}/reference-image/{image_id}",
    status_code=204,
)
async def delete_character_reference_image(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    image_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> None:
    try:
        await service.delete_reference_image(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
            image_id=image_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error deleting reference image {image_id} for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while deleting the reference image",
        )


@router.post(
    "/project/{project_id}/story/{story_id}/character/{character_id}/render/edit",
    status_code=201,
)
async def render_character_edit(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    body: CharacterRenderEditRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> ImageResponseSchema:
    """Edit an existing character render using fal's image-edit model.

    Optionally accepts a reference_image_id to guide the visual style of the edit.
    If provided, the reference image must already be uploaded and persisted as a
    CHARACTER_REFERENCE image for this character via POST .../upload-reference-image.

    Side-effect: the reference image (if provided) remains associated with this
    character and will continue to appear in the character's referenceImages list.
    It is not consumed or removed by this call.
    """
    try:
        image = await service.render_character_edit(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
            instruction=body.instruction,
            source_image_id=body.source_image_id,
            reference_image_id=body.reference_image_id,
        )
        return ImageResponseSchema.model_validate(image)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error editing render for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while editing the character render",
        )


@router.post(
    "/project/{project_id}/story/{story_id}/character/{character_id}/set-canonical-render",
    status_code=200,
)
async def set_canonical_render(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    body: SetCanonicalRenderRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRenderReferencesSchema:
    """Set a specific render as the canonical render for a character.

    The image must already exist as a CHARACTER_RENDER for this character.
    On success the canonical render shown in all character responses will be
    the chosen image rather than the most recently generated one.
    """
    try:
        character = await service.set_canonical_render(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            character_id=character_id,
            image_id=body.image_id,
        )
        render = await service.get_canonical_character_render(character.id)
        refs = await service.get_character_reference_images(character.id)
        return _build_character_full(character, render, refs)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error setting canonical render for character {character_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while setting the canonical render",
        )
