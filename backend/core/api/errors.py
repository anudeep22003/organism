from enum import StrEnum

from core.common import AliasedBaseModel


class AppErrorCode(StrEnum):
    AUTH_REQUIRED = "auth_required"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_TOKEN_INVALID = "auth_token_invalid"
    AUTH_REFRESH_REQUIRED = "auth_refresh_required"
    AUTH_REFRESH_INVALID = "auth_refresh_invalid"
    BILLING_ENTITLEMENT_REQUIRED = "billing_entitlement_required"


class AppErrorDetail(AliasedBaseModel):
    code: AppErrorCode
    message: str


def app_error_detail(*, code: AppErrorCode, message: str) -> dict[str, str]:
    return AppErrorDetail(code=code, message=message).model_dump()
