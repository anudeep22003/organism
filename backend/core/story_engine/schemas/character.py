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


class CharacterRenderReferencesSchema(CharacterResponseSchema):
    """Complete character payload: attributes, canonical render, and all reference images.

    Per Decision 12: embeds related images so the client needs no extra round-trips.
    """

    canonical_render: ImageResponseSchema | None = None
    reference_images: list[ImageResponseSchema] = []


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
