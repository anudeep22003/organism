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


class CharacterRenderReferencesSchema(AliasedBaseModel):
    """Complete character payload: attributes, canonical render, and all reference images.

    Per Decision 12: composes CharacterResponseSchema with image fields so the
    client receives everything in a single response with clear separation of concerns.
    """

    character: CharacterResponseSchema
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


class CharacterRenderEditRequest(AliasedBaseModel):
    instruction: str
    source_image_id: uuid.UUID
    reference_image_id: uuid.UUID | None = None
