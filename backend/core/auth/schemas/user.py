import uuid
from datetime import datetime

from pydantic import ConfigDict, EmailStr

from core.common import AliasedBaseModel


class UserSchemaBase(AliasedBaseModel):
    email: EmailStr

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
    id: uuid.UUID
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    created_at: datetime
    meta: dict

    model_config = ConfigDict(from_attributes=True)
