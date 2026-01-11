from typing import Annotated

from fastapi import APIRouter, Depends
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.services.database import get_async_db_session

from ..character_extractor import CharacterExtractor
from ..dependencies import get_verified_project
from ..models import Project
from ..state import ComicState

router = APIRouter(prefix="/phase", tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/extract-characters/{project_id}")
async def extract_characters(
    project: Annotated[Project, Depends(get_verified_project)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ComicState:
    logger.info(f"Extracting characters for project {project.id}")
    character_extractor = CharacterExtractor(project.id, db)
    memory = await character_extractor.run_and_return_updated_state()
    return memory
