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
from ...schemas.image import ImageResponseSchema
from ...schemas.panel import PanelResponseSchema, PanelWithRenderSchema
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
