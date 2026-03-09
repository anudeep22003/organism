import uuid
from datetime import datetime
from typing import Any

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
