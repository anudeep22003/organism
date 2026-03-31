import uuid
from datetime import datetime
from typing import Any

from core.common import AliasedBaseModel

from .image import ImageResponseSchema


class CharacterResponseSchema(AliasedBaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    source_event_id: uuid.UUID | None = None
    name: str
    slug: str
    attributes: dict[str, Any]
    meta: dict[str, Any]


class CharacterWithRenderSchema(CharacterResponseSchema):
    """Character response including the canonical render image (if any).

    Per Decision 12: composite schema embeds the latest character_render Image
    so the client can display it without an extra round-trip.
    """

    canonical_render: ImageResponseSchema | None = None


class CharacterUpdateSchema(AliasedBaseModel):
    name: str | None = None
    brief: str | None = None
    character_type: str | None = None
    era: str | None = None
    visual_form: str | None = None
    color_palette: list[str] | None = None
    distinctive_markers: list[str] | None = None
    demeanor: str | None = None
    role: str | None = None
    meta: dict[str, Any] | None = None


class CharacterRefineRequest(AliasedBaseModel):
    instruction: str
