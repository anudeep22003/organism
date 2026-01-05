import uuid
from datetime import datetime
from typing import Any

from pydantic import ConfigDict

from core.common import AliasedBaseModel


class ProjectSchemaBase(AliasedBaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreateSchema(ProjectSchemaBase):
    name: str | None = None
    user_id: uuid.UUID


class ProjectUpdateSchema(ProjectSchemaBase):
    state: dict[str, Any]


class ProjectResponseSchema(AliasedBaseModel):
    id: uuid.UUID
    name: str | None = None
    created_at: datetime
    updated_at: datetime
    state: dict[str, Any]
