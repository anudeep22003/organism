import uuid
from datetime import datetime

from pydantic import BaseModel


class AuthSessionSchemaBase(BaseModel):
    refresh_token_hash: str
    user_agent: str | None
    ip: str | None


class AuthSessionSchemaCreate(AuthSessionSchemaBase):
    user_id: uuid.UUID
    refresh_token_hash: str
    created_at: datetime
    expires_at: datetime


class AuthSessionSchemaRefresh(AuthSessionSchemaBase):
    refresh_token_hash: str
    created_at: datetime
    expires_at: datetime


class AuthSessionSchema(AuthSessionSchemaBase):
    id: uuid.UUID
    user_id: uuid.UUID
    refresh_token_hash: str
    created_at: datetime
    expires_at: datetime
