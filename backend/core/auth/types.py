from typing import Literal

from core.sockets.types.envelope import AliasedBaseModel

from .schemas.user import UserResponse


class LoginResponse(AliasedBaseModel):
    user: UserResponse | None = None
    status_code: Literal[
        "SUCCESS",
        "USER_NOT_FOUND",
        "INVALID_CREDENTIALS",
        "USER_ALREADY_EXISTS",
        "INTERNAL_ERROR",
    ]
