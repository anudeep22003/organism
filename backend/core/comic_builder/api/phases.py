from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_id
from core.auth.dependencies import get_session_manager
from core.auth.managers.session import SessionManager
from core.comic_builder.character_renderer import CharacterRenderer
from core.services.database import get_async_db_session
from core.sockets import sio

from ..character_extractor import CharacterExtractor
from ..consolidated_state import Character, ConsolidatedComicState
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


@router.post("/render-character/{project_id}")
async def render_character(
    project: Annotated[Project, Depends(get_verified_project)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    character: Character,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> dict:
    session = await session_manager.find_session_by_user_id(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Capture IDs before async operations to avoid expired session issues
    project_id = project.id
    session_id = str(session.id)

    character_renderer = CharacterRenderer(db)
    await character_renderer.execute_render_character_pipeline(project_id, character)
    await sio.emit("character_rendered", {"projectId": str(project_id)}, to=session_id)

    return {"message": "Character rendered successfully"}
