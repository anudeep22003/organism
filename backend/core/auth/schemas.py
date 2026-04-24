import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from core.common import AliasedBaseModel


class UserResponse(AliasedBaseModel):
    id: uuid.UUID
    email: str
    updated_at: datetime


class GoogleOAuthUserInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    email: str
    email_verified: bool = False
    name: str | None = None
    picture: str | None = None

    @field_validator("sub", "email")
    @classmethod
    def validate_required_string(cls, value: str) -> str:
        if value == "":
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("name", "picture", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if isinstance(value, str) and value != "":
            return value
        return None


class GoogleOAuthCallbackPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    access_token: str
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None
    expires_at: datetime | None = None
    userinfo: GoogleOAuthUserInfo

    @field_validator("access_token")
    @classmethod
    def validate_access_token(cls, value: str) -> str:
        if value == "":
            raise ValueError("Field cannot be empty")
        return value

    @field_validator("refresh_token", "id_token", "scope", mode="before")
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if isinstance(value, str) and value != "":
            return value
        return None

    @field_validator("expires_at", mode="before")
    @classmethod
    def parse_expires_at(cls, value: Any) -> Any:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        return value
