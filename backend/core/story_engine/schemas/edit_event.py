from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from core.common import AliasedBaseModel


class EditEventResponseSchema(AliasedBaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    operation_type: str
    user_instruction: str
    output_snapshot: dict[str, Any] | None = None
    status: str
    created_at: datetime
