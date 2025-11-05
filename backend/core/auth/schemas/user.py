import uuid
from datetime import datetime

from pydantic import ConfigDict

from core.sockets.types.envelope import AliasedBaseModel


class UserSchemaBase(AliasedBaseModel):
    email: str

    model_config = ConfigDict(from_attributes=True)


class UserSchemaCreate(UserSchemaBase):
    password: str


class UserSchemaSignin(UserSchemaBase):
    password: str


class UserSchema(UserSchemaBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    meta: dict


class UserResponse(UserSchemaBase):
    email: str
    id: uuid.UUID
    updated_at: datetime
