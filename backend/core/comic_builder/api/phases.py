import uuid
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user_id
from core.auth.dependencies import get_session_manager
from core.auth.managers.session import SessionManager
from core.services.database import get_async_db_session
from core.sockets import sio

from ..exceptions import (
    CharacterExtractorError,
    NoStoryError,
    RenderError,
    StoryGeneratorError,
)
from ..generation import (
    CharacterExtractor,
    CharacterRenderer,
    PanelGenerator,
    PanelRenderer,
    StoryPhase,
)
from ..schemas import SimpleEnvelope, StoryPromptRequest
from ..state import Character, ComicPanel, ConsolidatedComicState
from ..state_manager import ProjectStateManager
from .dependencies import verify_project_access

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


async def _story_envelope_stream(
    phase: StoryPhase, project_id: uuid.UUID, prompt: str
) -> AsyncGenerator[str, None]:
    """Wrap phase output in SimpleEnvelope JSON lines."""
    try:
        async for data in phase.execute_streaming(project_id, prompt):
            yield SimpleEnvelope(data=data).model_dump_json() + "\n"
    except StoryGeneratorError as e:
        logger.error(f"Story generation error for project {project_id}: {e}")
        yield SimpleEnvelope(data={"error": str(e)}).model_dump_json() + "\n"


@router.post("/generate-story/{project_id}")
async def generate_story(
    project_id: Annotated[uuid.UUID, Depends(verify_project_access)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    request: StoryPromptRequest,
) -> StreamingResponse:
    """Generate story for a project with streaming response.

    Streams story chunks as they are generated and persists the
    complete story to project state on completion.
    """
    logger.info(f"Generating story for project {project_id}")
    state_manager = ProjectStateManager(db)
    phase = StoryPhase(state_manager)
    return StreamingResponse(
        content=_story_envelope_stream(phase, project_id, request.story_prompt),
        media_type="application/x-ndjson",
    )

@router.post("/render-panel/{project_id}")
async def render_panel(
    project_id: Annotated[uuid.UUID, Depends(verify_project_access)],
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[AsyncSession, Depends(get_async_db_session)],
    panel: ComicPanel,
    session_manager: Annotated[SessionManager, Depends(get_session_manager)],
) -> dict:
    session = await session_manager.find_session_by_user_id(user_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Capture IDs before async operations to avoid expired session issues
    session_id = str(session.id)

    state_manager = ProjectStateManager(db)
    panel_renderer = PanelRenderer(state_manager)
    try:
        await panel_renderer.execute(project_id, panel)
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
            detail=f"An unexpected error occurred while rendering panel: [ref: {error_id}]",
        )

    await sio.emit("state.updated", {"projectId": str(project_id)}, to=session_id)

    return {"message": "Panel rendered successfully"}
