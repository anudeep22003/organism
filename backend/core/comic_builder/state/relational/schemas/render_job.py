from __future__ import annotations

import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from ..models.render_job import RenderableType, RenderJobStatus


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


class RenderJobResponseSchema(RenderJobSchemaBase):
    id: uuid.UUID
