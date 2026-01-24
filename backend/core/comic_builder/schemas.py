import uuid
from datetime import datetime
from typing import Any

from core.comic_builder.state import ConsolidatedComicState
from core.common import AliasedBaseModel


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
