import uuid
from datetime import datetime

from pydantic import EmailStr

from core.common import AliasedBaseModel


class UserSchemaBase(AliasedBaseModel):
    email: EmailStr


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
    id: uuid.UUID
    updated_at: datetime


class UserDetailResponse(UserResponse):
    created_at: datetime
    meta: dict
