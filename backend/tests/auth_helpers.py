import uuid

from core.auth.config import ACCESS_TOKEN_COOKIE_NAME
from core.auth.security import AccessTokenManager

_access_token_manager = AccessTokenManager()


def auth_cookie_header(user_id: uuid.UUID | str) -> dict[str, str]:
    if isinstance(user_id, str):
        user_id = uuid.UUID(user_id)

    token = _access_token_manager.create_access_token(user_id)
    return {"cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}"}
