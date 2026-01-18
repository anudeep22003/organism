from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_id
from core.auth.dependencies import get_session_manager
from core.auth.managers.session import SessionManager
from core.services.database import get_async_db_session
from core.sockets import sio

from ..character_extractor import CharacterExtractor
from ..consolidated_state import ConsolidatedComicState
from ..dependencies import get_verified_project
from ..models import Project

router = APIRouter(prefix="/phase", tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/extract-characters/{project_id}")
async def extract_characters(
    project: Annotated[Project, Depends(get_verified_project)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ConsolidatedComicState:
    logger.info(f"Extracting characters for project {project.id}")
    character_extractor = CharacterExtractor(project.id, db)
    memory = await character_extractor.run_and_return_updated_state()
    return memory


@router.get("/dummy")
async def dummy(
    user_id: Annotated[str, Depends(get_current_user_id)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> dict[str, str]:
    session = await session_manager.find_session_by_user_id(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # send a notification over websocket
    await sio.emit("dummy", "You are a dummy sent via websocket", to=str(session.id))
    return {"message": "You are a dummy straight via rest"}
