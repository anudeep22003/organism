import secrets
import uuid
from dataclasses import dataclass

import jwt

from core.common.utils import get_current_timestamp_seconds
from core.config import settings

from ..config import (
    ACCESS_TOKEN_TTL_SECONDS,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
)
from ..exceptions import (
    ExpiredAccessTokenError,
    InvalidAccessTokenError,
    InvalidRefreshTokenError,
)
from .hashers import PasswordHasher


@dataclass(frozen=True, slots=True)
class RefreshTokenParts:
    session_id: uuid.UUID
    secret: str


class AccessTokenManager:
    def create_access_token(self, user_id: uuid.UUID) -> str:
        now = get_current_timestamp_seconds()
        payload = {
            "sub": str(user_id),
            "iat": now,
            "exp": now + ACCESS_TOKEN_TTL_SECONDS,
            "jti": secrets.token_urlsafe(32),
            "iss": JWT_ISSUER,
            "aud": JWT_AUDIENCE,
        }
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=JWT_ALGORITHM,
        )

    def extract_user_id(self, access_token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                access_token,
                settings.jwt_secret_key,
                algorithms=[JWT_ALGORITHM],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredAccessTokenError from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidAccessTokenError from exc

        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise InvalidAccessTokenError("Access token missing subject")

        try:
            return uuid.UUID(user_id)
        except ValueError as exc:
            raise InvalidAccessTokenError("Access token subject is not a UUID") from exc


class RefreshTokenManager:
    def __init__(self, password_hasher: PasswordHasher) -> None:
        self.password_hasher = password_hasher

    def create_refresh_token(self, session_id: uuid.UUID) -> tuple[str, str]:
        secret = secrets.token_urlsafe(32)
        token = f"{session_id}.{secret}"
        secret_hash = self.hash_refresh_token_secret(secret)
        return token, secret_hash

    def parse_refresh_token(self, refresh_token: str) -> RefreshTokenParts:
        try:
            session_id_str, secret = refresh_token.split(".", 1)
            session_id = uuid.UUID(session_id_str)
        except ValueError as exc:
            raise InvalidRefreshTokenError("Malformed refresh token") from exc

        if not secret:
            raise InvalidRefreshTokenError("Malformed refresh token")

        return RefreshTokenParts(session_id=session_id, secret=secret)

    def hash_refresh_token_secret(self, secret: str) -> str:
        return self.password_hasher.hash(secret)

    def verify_refresh_token_secret(self, secret: str, expected_hash: str) -> bool:
        return self.password_hasher.verify(secret, expected_hash)
