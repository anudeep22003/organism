"""
Pydantic schemas for the panel pipeline.

Naming conventions:
  - PanelContent / GeneratedPanelsResponse: instructor structured extraction models
  - PanelResponseSchema: API response for a single panel (no render)
  - PanelWithRenderSchema: API response for a single panel including canonical render
"""

import uuid
from datetime import datetime
from typing import Any

from core.common import AliasedBaseModel

from .image import ImageResponseSchema


class PanelContentBase(AliasedBaseModel):
    """Stable panel fields shared across all panel content models.

    Does not include `characters` — that field is injected at runtime with a
    Literal constraint built from the story's actual character slugs, so the
    LLM is forced to pick from the exact slugs stored in the DB.

    Used as __base__ in create_model(...) calls inside PanelService.
    """

    background: str
    dialogue: str


class PanelContent(PanelContentBase):
    """Concrete panel schema with unconstrained characters.

    Used as the return type annotation from LLM helper methods and as the
    response_model for _regenerate_panel (where existing slugs are already
    correct and the constraint is less critical).
    """

    characters: list[str]  # slugs


class GeneratedPanelsResponse(AliasedBaseModel):
    """Top-level instructor response wrapping a list of panels."""

    panels: list[PanelContent]


class PanelResponseSchema(AliasedBaseModel):
    """Panel response without an embedded render (used in list/generate endpoints)."""

    id: uuid.UUID
    story_id: uuid.UUID
    source_event_id: uuid.UUID | None = None
    order_index: int
    attributes: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PanelWithRenderSchema(PanelResponseSchema):
    """Panel response including the canonical render image (if any).

    Same composite pattern as CharacterWithRenderSchema (Decision 12).
    """

    canonical_render: ImageResponseSchema | None = None


class PanelGenerateRequest(AliasedBaseModel):
    """Request body for the single-panel generate/regenerate endpoint.

    instruction is optional — absent on first generation, present on regeneration.
    """

    instruction: str | None = None


class PanelRenderEditRequest(AliasedBaseModel):
    """Request body for editing an existing panel render via fal image-edit model."""

    instruction: str
    source_image_id: uuid.UUID
