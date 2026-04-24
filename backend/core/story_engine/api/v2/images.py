import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from core.auth.api import get_current_user_id

from ...exceptions import NotFoundError
from ...schemas.image import ImageSignedUrlResponseSchema
from ...service import ImageService
from ..dependencies import get_image_service

router = APIRouter(tags=["images", "v2"])


@router.get("/image/{image_id}/signed-url", status_code=200)
async def get_image_signed_url(
    image_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ImageService, Depends(get_image_service)],
) -> ImageSignedUrlResponseSchema:
    try:
        url, expires_at = await service.get_signed_url(image_id, user_id)
        return ImageSignedUrlResponseSchema(url=url, expires_at=expires_at)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error generating signed URL for image {image_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the signed URL",
        )
