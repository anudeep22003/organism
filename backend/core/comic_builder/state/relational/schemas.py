from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from ...state import ConsolidatedComicState
from .models import RenderableType, RenderJobStatus


class ProjectSchemaBase(AliasedBaseModel):
    name: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    pass


class ProjectCreateSchema(ProjectSchemaBase):
    name: str | None = None


class ProjectUpdateSchema(ProjectSchemaBase):
    name: str | None = None
    state: ConsolidatedComicState


class ProjectResponseSchema(ProjectSchemaBase):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime
    updated_at: datetime
    state: dict[str, Any]


class ProjectListResponseSchema(ProjectSchemaBase):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime
    updated_at: datetime


class StorySchemaBase(AliasedBaseModel):
    story_text: str = ""
    user_input_text: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class StoryCreateSchema(StorySchemaBase):
    project_id: uuid.UUID


class StoryUpdateSchema(AliasedBaseModel):
    story_text: str | None = None
    user_input_text: list[str] | None = None
    meta: dict[str, Any] | None = None


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


class RenderJobSchemaBase(AliasedBaseModel):
    renderable_id: uuid.UUID
    renderable_type: RenderableType
    output_url: str | None = None
    prompt: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)
    user_input_text: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)
    status: RenderJobStatus = RenderJobStatus.PENDING


class RenderJobCreateSchema(RenderJobSchemaBase):
    pass


class RenderJobUpdateSchema(AliasedBaseModel):
    output_url: str | None = None
    prompt: str | None = None
    inputs: dict[str, Any] | None = None
    user_input_text: list[str] | None = None
    meta: dict[str, Any] | None = None
    status: RenderJobStatus | None = None


class StoryResponseSchema(StorySchemaBase):
    id: uuid.UUID
    project_id: uuid.UUID


class CharacterResponseSchema(CharacterSchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID


class ComicPanelResponseSchema(ComicPanelSchemaBase):
    id: uuid.UUID
    story_id: uuid.UUID
    characters: list[CharacterResponseSchema] = Field(default_factory=list)


class RenderJobResponseSchema(RenderJobSchemaBase):
    id: uuid.UUID


class StoryCharacterResponseSchema(AliasedBaseModel):
    story_id: uuid.UUID
    character_id: uuid.UUID
    meta: dict[str, Any] = Field(default_factory=dict)


class PanelCharacterResponseSchema(AliasedBaseModel):
    panel_id: uuid.UUID
    character_id: uuid.UUID
    meta: dict[str, Any] = Field(default_factory=dict)


class ProjectRelationalStateSchema(AliasedBaseModel):
    project_id: uuid.UUID
    stories: list[StoryResponseSchema] = Field(default_factory=list)
    characters: list[CharacterResponseSchema] = Field(default_factory=list)
    panels: list[ComicPanelResponseSchema] = Field(default_factory=list)
