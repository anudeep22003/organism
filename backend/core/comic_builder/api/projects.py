from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger

from core.auth.dependencies import get_current_user_id

router = APIRouter(tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/projects")
async def get_projects(user_id: Annotated[str, Depends(get_current_user_id)]) -> list:
    logger.info(f"Getting projects for user {user_id}")
    return []
