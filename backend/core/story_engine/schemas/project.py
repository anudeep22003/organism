from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from ..state.consolidated import ConsolidatedComicState
from .character import CharacterResponseSchema
from .panel import ComicPanelResponseSchema
from .story import StoryResponseSchema


class ProjectSchemaBase(AliasedBaseModel):
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
    story_count: int


class ProjectRelationalStateSchema(ProjectResponseSchema):
    stories: list[StoryResponseSchema] = Field(default_factory=list)
    characters: list[CharacterResponseSchema] = Field(default_factory=list)
    panels: list[ComicPanelResponseSchema] = Field(default_factory=list)
