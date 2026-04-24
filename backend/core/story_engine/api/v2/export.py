import uuid
from io import BytesIO
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.api import get_current_user_id
from core.services.database import get_async_db_session

from ...exceptions import ExportError, NotFoundError
from ...service.export_service import ExportService

router = APIRouter(tags=["export", "v2"])


async def get_export_service(
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ExportService:
    return ExportService(db_session=db)


@router.get("/project/{project_id}/story/{story_id}/export/zip")
async def export_zip(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ExportService, Depends(get_export_service)],
) -> StreamingResponse:
    try:
        data = await service.export_as_zip(project_id, story_id)
        return StreamingResponse(
            BytesIO(data),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="comic-{story_id}.zip"'
            },
        )
    except ExportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error exporting ZIP for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/project/{project_id}/story/{story_id}/export/instagram")
async def export_instagram(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ExportService, Depends(get_export_service)],
) -> StreamingResponse:
    try:
        data = await service.export_as_instagram_zip(project_id, story_id)
        return StreamingResponse(
            BytesIO(data),
            media_type="application/zip",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="comic-{story_id}-instagram.zip"'
                )
            },
        )
    except ExportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error exporting Instagram ZIP for story {story_id}: {e}"
        )
        raise HTTPException(status_code=500, detail="Export failed")


@router.get("/project/{project_id}/story/{story_id}/export/pdf")
async def export_pdf(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[ExportService, Depends(get_export_service)],
) -> StreamingResponse:
    try:
        data = await service.export_as_pdf(project_id, story_id)
        return StreamingResponse(
            BytesIO(data),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="comic-{story_id}.pdf"'
            },
        )
    except ExportError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error exporting PDF for story {story_id}: {e}")
        raise HTTPException(status_code=500, detail="Export failed")
