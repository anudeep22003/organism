from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel


class CharacterSchemaBase(AliasedBaseModel):
    name: str
    slug: str
    brief: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
    user_input_text: list[str] = Field(default_factory=list)
    reference_image_urls: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)


class CharacterCreateSchema(CharacterSchemaBase):
    user_id: uuid.UUID


class CharacterUpdateSchema(AliasedBaseModel):
    name: str | None = None
    slug: str | None = None
    brief: str | None = None
    attributes: dict[str, Any] | None = None
    user_input_text: list[str] | None = None
    reference_image_urls: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


class CharacterResponseSchema(CharacterSchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
