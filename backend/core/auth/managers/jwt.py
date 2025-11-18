import secrets
import uuid
from typing import Any

import jwt
from loguru import logger

from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_seconds

from ..config import (
    ACCESS_TOKEN_TTL_SECONDS,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    JWT_SECRET_KEY,
)
from ..exceptions import (
    ExpiredTokenError,
    InvalidTokenError,
)
from ..managers.password import get_password_hasher

logger = logger.bind(name=__name__)


class JWTPayload(AliasedBaseModel):
    sub: str
    iat: int
    exp: int
    jti: str
    issuer: str
    audience: str


class JWTTokenManager:
    def __init__(self) -> None:
        self.password_context = get_password_hasher()

    def create_access_token(self, user_id: str | uuid.UUID) -> str:
        """
        Create a new JWT access token for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            Encoded JWT token string
        """
        if isinstance(user_id, uuid.UUID):
            user_id = str(user_id)

        iat = get_current_timestamp_seconds()
        exp = iat + ACCESS_TOKEN_TTL_SECONDS
        jti = secrets.token_urlsafe(32)
        payload = JWTPayload(
            sub=user_id,
            iat=iat,
            exp=exp,
            jti=jti,
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
        )
        return jwt.encode(payload.model_dump(), JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self) -> str:
        refresh_token = secrets.token_urlsafe(32)
        return refresh_token

    def decode_access_token(self, access_token: str) -> Any:
        try:
            decoded = jwt.decode(
                access_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
            )
            logger.debug(f"type of decoded is: {type(decoded)}")
            return decoded
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError
        except jwt.InvalidTokenError:
            raise InvalidTokenError
        except Exception as e:
            raise InvalidTokenError(f"Invalid token: {e}")

    def extract_user_id_from_access_token(self, access_token: str) -> str:
        payload = self.decode_access_token(access_token)
        user_id = payload.get("sub")

        if not user_id:
            raise InvalidTokenError("User ID not found in access token")

        if not isinstance(user_id, str):
            raise Exception("User ID is not a string")

        return user_id
