from typing import Final, Literal

from core.config import settings

JWT_ALGORITHM: Final[str] = "HS256"
JWT_ISSUER: Final[str] = "backend-auth"
JWT_AUDIENCE: Final[str] = "frontend-app"

ACCESS_TOKEN_TTL_SECONDS: Final[int] = 30 * 60
REFRESH_TOKEN_TTL_SECONDS: Final[int] = 10 * 24 * 60 * 60

ACCESS_TOKEN_COOKIE_NAME: Final[str] = "access_token"
ACCESS_TOKEN_COOKIE_PATH: Final[str] = "/"
ACCESS_TOKEN_COOKIE_HTTPONLY: Final[bool] = True
ACCESS_TOKEN_COOKIE_SECURE: Final[bool] = settings.env == "production"
ACCESS_TOKEN_COOKIE_SAMESITE: Final[Literal["lax", "strict", "none"]] = "lax"

REFRESH_TOKEN_COOKIE_NAME: Final[str] = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH: Final[str] = "/api/auth"
REFRESH_TOKEN_COOKIE_HTTPONLY: Final[bool] = True
REFRESH_TOKEN_COOKIE_SECURE: Final[bool] = settings.env == "production"
REFRESH_TOKEN_COOKIE_SAMESITE: Final[Literal["lax", "strict", "none"]] = "lax"
