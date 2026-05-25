from enum import StrEnum

from core.common import AliasedBaseModel


class AuthErrorCode(StrEnum):
    AUTH_REQUIRED = "auth_required"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_TOKEN_INVALID = "auth_token_invalid"
    AUTH_REFRESH_REQUIRED = "auth_refresh_required"
    AUTH_REFRESH_INVALID = "auth_refresh_invalid"
    AUTH_USER_NOT_FOUND = "auth_user_not_found"
    AUTH_RATE_LIMITED = "auth_rate_limited"


class AuthErrorDetail(AliasedBaseModel):
    code: AuthErrorCode
    message: str
