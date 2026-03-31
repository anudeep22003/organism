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


class PanelContent(AliasedBaseModel):
    """Single panel as produced by the LLM structured extraction.

    characters contains character slugs — resolved to UUIDs at insert time.
    """

    background: str
    characters: list[str]  # slugs
    dialogue: str


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
