import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_id
from core.auth.dependencies import get_session_manager
from core.auth.managers.session import SessionManager
from core.services.database import get_async_db_session
from core.sockets import sio

from ..character_extractor import (
    CharacterExtractor,
    CharacterExtractorError,
    NoStoryError,
)
from ..character_renderer import CharacterRenderer, RenderError
from ..consolidated_state import Character, ConsolidatedComicState
from ..dependencies import verify_project_access
from ..panel_generator import PanelGenerator
from ..project_state_manager import ProjectStateManager

router = APIRouter(prefix="/phase", tags=["comic", "builder"])

logger = logger.bind(name=__name__)


@router.get("/extract-characters/{project_id}")
async def extract_characters(
    project_id: Annotated[uuid.UUID, Depends(verify_project_access)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
) -> ConsolidatedComicState:
    logger.info(f"Extracting characters for project {project_id}")
    try:
        state_manager = ProjectStateManager(db)
        character_extractor = CharacterExtractor(state_manager)
        memory = await character_extractor.execute(project_id)
        return memory
    except NoStoryError:
        logger.warning(
            f"No story available for project {project_id}, generate store first"
        )
        raise HTTPException(
            status_code=400,
            detail="No story available for project, generate store first",
        )
    except CharacterExtractorError as e:
        logger.warning(f"Error extracting characters: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while extracting characters"
        )
    except Exception as e:
        error_id = uuid.uuid4().hex[:8]
        logger.exception(f"Unexpected error extracting characters: [ref: {error_id}]")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while extracting characters: [ref: {error_id}]",
        ) from e


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
    project_id: Annotated[uuid.UUID, Depends(verify_project_access)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    character: Character,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> dict:
    session = await session_manager.find_session_by_user_id(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Capture IDs before async operations to avoid expired session issues
    session_id = str(session.id)

    state_manager = ProjectStateManager(db)
    character_renderer = CharacterRenderer(state_manager)
    try:
        await character_renderer.execute(project_id, character)
    except RenderError as e:
        logger.error(f"Error rendering character: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        error_id = uuid.uuid4().hex[
            :8
        ]  # first 8 characters of the UUID without the hyphens (hex removes the hyphens)
        logger.exception(f"Unexpected error rendering character: [ref: {error_id}]")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while rendering character: [ref: {error_id}]",
        )

    await sio.emit("state.updated", {"projectId": str(project_id)}, to=session_id)

    return {"message": "Character rendered successfully"}


@router.get("/generate-panels/{project_id}")
async def generate_panels(
    project_id: Annotated[uuid.UUID, Depends(verify_project_access)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> dict:
    session = await session_manager.find_session_by_user_id(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Capture IDs before async operations to avoid expired session issues
    session_id = str(session.id)

    state_manager = ProjectStateManager(db)
    panel_generator = PanelGenerator(state_manager)
    await panel_generator.execute(project_id)
    await sio.emit("state.updated", {"projectId": str(project_id)}, to=session_id)
    return {"message": "Panels generated successfully"}
