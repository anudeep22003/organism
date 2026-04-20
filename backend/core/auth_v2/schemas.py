import uuid
from datetime import datetime

from core.common import AliasedBaseModel


class UserResponse(AliasedBaseModel):
    id: uuid.UUID
    email: str
    updated_at: datetime
