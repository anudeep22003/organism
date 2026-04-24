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
from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger

from core.auth_v2.api import get_current_user_id

from ...exceptions import (
    NoCharactersError,
    NoStoryTextError,
    NotFoundError,
    PanelAlreadyGeneratedError,
    UploadImageError,
)
from ...schemas.edit_event import EditEventResponseSchema
from ...schemas.image import ImageResponseSchema
from ...schemas.panel import (
    PanelRefineRequest,
    PanelRenderEditRequest,
    PanelRenderReferencesSchema,
    PanelResponseSchema,
    SetCanonicalPanelRenderRequest,
)
from ...service import PanelService
from ..dependencies import get_panel_service

router = APIRouter(tags=["panels", "v2"])


def _build_panel_full(
    panel: object,
    image: object | None,
    reference_images: Sequence[object] | None = None,
) -> PanelRenderReferencesSchema:
    """Assemble a PanelRenderReferencesSchema from ORM objects.

    Panel data is nested under 'panel', image fields sit at top level.
    Symmetric with _build_character_full in character.py.
    """
    return PanelRenderReferencesSchema(
        panel=PanelResponseSchema.model_validate(panel),
        canonical_render=ImageResponseSchema.model_validate(image) if image else None,
        reference_images=[
            ImageResponseSchema.model_validate(r) for r in (reference_images or [])
        ],
    )


# ---------------------------------------------------------------------------
# Story 110 — Delete a single panel
# ---------------------------------------------------------------------------


@router.delete(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}",
    status_code=204,
)
async def delete_panel(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> None:
    """Hard-delete a panel and its associated render images."""
    try:
        await service.delete_panel(project_id, story_id, panel_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error deleting panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while deleting the panel",
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
) -> list[PanelRenderReferencesSchema]:
    """Return all panels for a story ordered by order_index, with canonical renders."""
    try:
        pairs = await service.get_panels(project_id, story_id)
        return [_build_panel_full(panel, render) for panel, render in pairs]
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
) -> PanelRenderReferencesSchema:
    """Return a single panel by ID, with canonical render."""
    try:
        panel, render = await service.get_panel(project_id, story_id, panel_id)
        return _build_panel_full(panel, render)
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
) -> PanelRenderReferencesSchema:
    """Generate content for a single panel for the first time.

    Only valid when the panel has no content yet. Returns 400 if the panel
    already has generated content — use POST .../refine to update it.
    """
    try:
        panel = await service.generate_panel(
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
        )
        render = await service.get_canonical_panel_render(panel_id)
        return _build_panel_full(panel, render)
    except PanelAlreadyGeneratedError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoCharactersError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error generating panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating the panel",
        )


# ---------------------------------------------------------------------------
# Story 55 — Refine panel attributes via user instruction
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/refine",
    status_code=200,
)
async def refine_panel(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    body: PanelRefineRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> PanelRenderReferencesSchema:
    """Refine a panel's attributes using a user instruction.

    The panel must already have content (i.e. generate must have been called first).
    Returns the full panel payload with updated attributes. Mirrors POST .../character/:id/refine.
    """
    try:
        panel = await service.refine_panel(
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            instruction=body.instruction,
        )
        render = await service.get_canonical_panel_render(panel_id)
        refs = await service.get_panel_reference_images(panel_id)
        return _build_panel_full(panel, render, refs)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoCharactersError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error refining panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while refining the panel",
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
) -> PanelRenderReferencesSchema:
    """Render a panel image via fal and store in GCS.

    Returns the full panel payload including the new canonical render and
    reference images — mirrors render_character which returns the full
    CharacterRenderReferencesSchema so the client can update its cache slot.
    """
    try:
        panel, image = await service.render_panel(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
        )
        refs = await service.get_panel_reference_images(panel_id)
        return _build_panel_full(panel, image, refs)
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
# Story 80 — Panel edit history
# ---------------------------------------------------------------------------


@router.get(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/history",
    status_code=200,
)
async def get_panel_history(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
    limit: int = 20,
) -> list[EditEventResponseSchema]:
    """Return the edit history for a panel — all GENERATE_PANEL and RENDER_PANEL events."""
    try:
        events = await service.get_panel_history(
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            limit=limit,
        )
        return [EditEventResponseSchema.model_validate(e) for e in events]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error getting history for panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while getting panel history",
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
) -> list[PanelRenderReferencesSchema]:
    """Generate all panels for a story from its story text.

    Calls the LLM to extract structured panel content, persists each panel
    with a per-panel EditEvent(GENERATE_PANEL, SUCCEEDED).
    No render exists at this point, so canonical_render is always None.
    """
    try:
        panels = await service.generate_panels(project_id, story_id)
        return [_build_panel_full(p, None) for p in panels]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NoStoryTextError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except NoCharactersError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error generating panels for story {story_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while generating panels",
        )


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/render/edit",
    status_code=201,
)
async def render_panel_edit(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    body: PanelRenderEditRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> ImageResponseSchema:
    """Edit an existing panel render using fal's image-edit model.

    Optionally accepts a reference_image_id to guide the visual style of the edit.
    If provided, the reference image must already exist as a render for this panel.

    Side-effect: the reference image (if provided) is not consumed or removed by
    this call — it remains associated with the panel independently.
    """
    try:
        image = await service.render_panel_edit(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            instruction=body.instruction,
            source_image_id=body.source_image_id,
            reference_image_id=body.reference_image_id,
        )
        return ImageResponseSchema.model_validate(image)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Unexpected error editing render for panel {panel_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while editing the panel render",
        )


# ---------------------------------------------------------------------------
# set-canonical-render
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/set-canonical-render",
    status_code=200,
)
async def set_canonical_render(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    body: SetCanonicalPanelRenderRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> PanelRenderReferencesSchema:
    """Set a specific render image as the canonical render for a panel.

    The chosen image must already exist as a PANEL_RENDER for this panel.
    Returns the full panel payload with the updated canonical render.
    """
    try:
        panel = await service.set_canonical_render(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            image_id=body.image_id,
        )
        render = await service.get_canonical_panel_render(panel.id)
        return _build_panel_full(panel, render)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error setting canonical render for panel {panel_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while setting the canonical render",
        )


# ---------------------------------------------------------------------------
# upload-reference-image
# ---------------------------------------------------------------------------


@router.post(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/upload-reference-image",
    status_code=status.HTTP_201_CREATED,
)
async def upload_reference_image(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
    image: UploadFile = File(...),
) -> PanelRenderReferencesSchema:
    """Upload a reference image for a panel.

    The uploaded image is stored as a PANEL_REFERENCE and returned in the
    referenceImages list of the full panel payload.
    """
    try:
        await service.upload_reference_image(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            image=image,
        )
        panel, render = await service.get_panel(project_id, story_id, panel_id)
        refs = await service.get_panel_reference_images(panel_id)
        return _build_panel_full(panel, render, refs)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UploadImageError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error uploading reference image for panel {panel_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while uploading the reference image",
        )


# ---------------------------------------------------------------------------
# reference-images (list)
# ---------------------------------------------------------------------------


@router.get(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/reference-images",
    status_code=200,
)
async def list_panel_reference_images(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> list[ImageResponseSchema]:
    """Return all reference images for a panel, ordered newest first."""
    try:
        # Verify panel exists within story/project scope
        await service.get_panel(project_id, story_id, panel_id)
        images = await service.get_panel_reference_images(panel_id)
        return [ImageResponseSchema.model_validate(img) for img in images]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error listing reference images for panel {panel_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while listing reference images",
        )


# ---------------------------------------------------------------------------
# delete-reference-image
# ---------------------------------------------------------------------------


@router.delete(
    "/project/{project_id}/story/{story_id}/panel/{panel_id}/reference-image/{image_id}",
    status_code=204,
)
async def delete_panel_reference_image(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    image_id: uuid.UUID,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
    service: Annotated[PanelService, Depends(get_panel_service)],
) -> None:
    """Delete a reference image from a panel."""
    try:
        await service.delete_reference_image(
            user_id=user_id,
            project_id=project_id,
            story_id=story_id,
            panel_id=panel_id,
            image_id=image_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(
            f"Unexpected error deleting reference image {image_id} for panel {panel_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while deleting the reference image",
        )
