import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuthSessionSchemaBase(BaseModel):
    refresh_token_hash: str
    user_agent: str | None
    ip: str | None

    model_config = ConfigDict(from_attributes=True)


class AuthSessionSchema(AuthSessionSchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None = None
    last_used_at: datetime
