from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel


class StorySchemaBase(AliasedBaseModel):
    story_text: str = ""
    user_input_text: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class StoryCreateSchema(StorySchemaBase):
    project_id: uuid.UUID


class StoryResponseSchema(StorySchemaBase):
    id: uuid.UUID
    project_id: uuid.UUID


class GenerateStoryRequest(AliasedBaseModel):
    story_prompt: str
