import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.dependencies import get_current_user_id
from core.services.database import get_async_db_session

router = APIRouter(prefix="/phase", tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/extract-characters/{project_id}")
async def extract_characters(
    project_id: uuid.UUID,
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> dict[str, str]:
    logger.info(f"Extracting characters for project {project_id}")
    return {"message": "Extracting characters..."}
