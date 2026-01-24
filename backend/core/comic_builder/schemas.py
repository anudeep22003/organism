import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from core.comic_builder.state import ConsolidatedComicState
from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_seconds


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


class SimpleEnvelope(AliasedBaseModel):
    """Envelope for streaming responses."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(default_factory=get_current_timestamp_seconds)

    request_id: str | None = None
    stream_id: str | None = None
    seq: int | None = None

    data: dict[str, Any]


class StoryPromptRequest(AliasedBaseModel):
    """Request schema for story generation."""

    story_prompt: str
