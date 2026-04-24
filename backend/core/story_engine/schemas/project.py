from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field

from core.common import AliasedBaseModel

from .story import StoryResponseSchema


class ProjectSchemaBase(AliasedBaseModel):
    pass


class ProjectCreateSchema(ProjectSchemaBase):
    name: str | None = None


class ProjectRenameSchema(ProjectSchemaBase):
    name: str


class ProjectUpdateSchema(ProjectSchemaBase):
    name: str | None = None


class ProjectResponseSchema(ProjectSchemaBase):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponseSchema(ProjectSchemaBase):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime
    updated_at: datetime
    story_count: int


class ProjectRelationalStateSchema(ProjectResponseSchema):
    stories: list[StoryResponseSchema] = Field(default_factory=list)
