from __future__ import annotations

import uuid
from datetime import datetime

from core.common import AliasedBaseModel


class EditEventResponseSchema(AliasedBaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    operation_type: str
    user_instruction: str
    status: str
    created_at: datetime
