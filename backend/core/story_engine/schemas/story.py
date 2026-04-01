from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel


class StorySchemaBase(AliasedBaseModel):
    story_text: str = ""
    user_input_text: str = ""
    meta: dict[str, Any] = Field(default_factory=dict)


class StoryCreateSchema(StorySchemaBase):
    pass


class StoryResponseSchema(StorySchemaBase):
    id: uuid.UUID
    project_id: uuid.UUID
    source_event_id: uuid.UUID | None = None


class GenerateStoryRequest(AliasedBaseModel):
    story_prompt: str
