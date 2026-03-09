import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from core.common import AliasedBaseModel


class CharacterSchemaBase(AliasedBaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CharacterResponseSchema(CharacterSchemaBase):
    name: str
    slug: str
    attributes: dict[str, Any]
    meta: dict[str, Any]


class CharacterUpdateSchema(BaseModel):
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
