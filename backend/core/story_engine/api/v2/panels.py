"""
Panel API endpoints — v2.

Stories covered here:
  20 — POST /panels/generate
  30 — GET  /panels
  40 — GET  /panel/{panel_id}
  50 — POST /panel/{panel_id}/generate
  60 — POST /panel/{panel_id}/render
  70 — GET  /panel/{panel_id}/renders
  80 — GET  /panel/{panel_id}/history
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from core.auth.dependencies import get_current_user_id

from ...exceptions import NoStoryTextError, NotFoundError
from ...models.image import ImageDiscriminatorKey
from ...schemas.image import ImageResponseSchema
from ...schemas.panel import (
    PanelGenerateRequest,
    PanelResponseSchema,
    PanelWithRenderSchema,
)
from ...service import PanelService
from ..dependencies import get_panel_service

router = APIRouter(tags=["panels", "v2"])


def _build_panel_with_render(
    panel: object, image: object | None
) -> PanelWithRenderSchema:
    """Assemble a PanelWithRenderSchema from ORM objects (per Decision 12)."""
    return PanelWithRenderSchema(
        **PanelResponseSchema.model_validate(panel).model_dump(),
        canonical_render=ImageResponseSchema.model_validate(image) if image else None,
    )


# ---------------------------------------------------------------------------
# Story 30 — List panels for a story
# ---------------------------------------------------------------------------


@router.get(
    "/project/{project_id}/story/{story_id}/panels",
    status_code=200,
)
async def list_panels(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> list[PanelWithRenderSchema]:
    """Return all panels for a story ordered by order_index, with canonical renders."""
    try:
        pairs = await service.get_panels(project_id, story_id)
        return [_build_panel_with_render(panel, render) for panel, render in pairs]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error listing panels for story {story_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while listing panels",
        )


# ---------------------------------------------------------------------------
# Story 40 — Get a single panel
# ---------------------------------------------------------------------------


@router.get(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}",
    status_code=200,
)
async def get_panel(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> PanelWithRenderSchema:
    """Return a single panel by ID, with canonical render."""
    try:
        panel, render = await service.get_panel(project_id, story_id, panel_id)
        return _build_panel_with_render(panel, render)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error getting panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while getting the panel",
        )


# ---------------------------------------------------------------------------
# Story 50 — Single panel generate / regenerate
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/generate",
    status_code=200,
)
async def generate_panel(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
    body: PanelGenerateRequest | None = None,
) -> PanelWithRenderSchema:
    """Generate or regenerate content for a single panel (Decision 8).

    First call (empty attributes): generates from story context.
    Subsequent calls: refines using the optional instruction.
    """
    try:
        panel = await service.generate_panel(
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            instruction=body.instruction if body is not None else None,
        )
        render = await service.repository_v2.image.get_canonical_render(
            target_id=panel_id,
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )
        return _build_panel_with_render(panel, render)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the panel",
        )


# ---------------------------------------------------------------------------
# Story 60 — Render a panel image
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/render",
    status_code=200,
)
async def render_panel(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> ImageResponseSchema:
    """Render a panel image via fal and store in GCS.

    Returns the created Image ORM object serialized as ImageResponseSchema.
    The panel's updated canonical render is visible on subsequent GET /panel/{id} calls.
    """
    try:
        image = await service.render_panel(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
        )
        return ImageResponseSchema.model_validate(image)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error rendering panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while rendering the panel",
        )


# ---------------------------------------------------------------------------
# Story 70 — List all render variations for a panel
# ---------------------------------------------------------------------------


@router.get(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/renders",
    status_code=200,
)
async def list_panel_renders(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> list[ImageResponseSchema]:
    """Return all render variations for a panel, ordered newest first."""
    try:
        images = await service.get_panel_renders(project_id, story_id, panel_id)
        return [ImageResponseSchema.model_validate(img) for img in images]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error listing renders for panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while listing panel renders",
        )


# ---------------------------------------------------------------------------
# Story 20 — Bulk panel generation
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panels/generate",
    status_code=201,
)
async def generate_panels(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> list[PanelResponseSchema]:
    """Generate all panels for a story from its story text.

    Calls the LLM to extract structured panel content, persists each panel
    with a per-panel EditEvent(GENERATE_PANEL, SUCCEEDED).
    """
    try:
        panels = await service.generate_panels(project_id, story_id)
        return [PanelResponseSchema.model_validate(p) for p in panels]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoStoryTextError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error generating panels for story {story_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating panels",
        )
