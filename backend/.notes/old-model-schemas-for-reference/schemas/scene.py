from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from .character import CharacterResponseSchema


class SceneSchemaBase(AliasedBaseModel):
    scene_order: int
    background: str = ""
    dialogue: str = ""
    user_input_text: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class SceneCreateSchema(SceneSchemaBase):
    story_id: uuid.UUID


class SceneUpdateSchema(AliasedBaseModel):
    scene_order: int | None = None
    background: str | None = None
    dialogue: str | None = None
    user_input_text: list[str] | None = None
    meta: dict[str, Any] | None = None


class SceneResponseSchema(SceneSchemaBase):
    id: uuid.UUID
    story_id: uuid.UUID
    characters: list[CharacterResponseSchema] = Field(default_factory=list)


class SceneCharacterResponseSchema(AliasedBaseModel):
    scene_id: uuid.UUID
    character_id: uuid.UUID
    meta: dict[str, Any] = Field(default_factory=dict)
