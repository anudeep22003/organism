from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from .character import CharacterResponseSchema


class ComicPanelSchemaBase(AliasedBaseModel):
    panel_order: int
    background: str = ""
    dialogue: str = ""
    user_input_text: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class ComicPanelCreateSchema(ComicPanelSchemaBase):
    story_id: uuid.UUID


class ComicPanelUpdateSchema(AliasedBaseModel):
    panel_order: int | None = None
    background: str | None = None
    dialogue: str | None = None
    user_input_text: list[str] | None = None
    meta: dict[str, Any] | None = None


class ComicPanelResponseSchema(ComicPanelSchemaBase):
    id: uuid.UUID
    story_id: uuid.UUID
    characters: list[CharacterResponseSchema] = Field(default_factory=list)


class PanelCharacterResponseSchema(AliasedBaseModel):
    panel_id: uuid.UUID
    character_id: uuid.UUID
    meta: dict[str, Any] = Field(default_factory=dict)
