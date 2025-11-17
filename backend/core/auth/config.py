"""Authentication configuration and constants."""

from typing import Final, Literal

# JWT Configuration
JWT_ALGORITHM: Final[str] = "HS256"
JWT_ISSUER: Final[str] = "backend-auth-service"
JWT_AUDIENCE: Final[str] = "frontend-app"

# Token Lifetimes (in seconds)
ACCESS_TOKEN_TTL_SECONDS: Final[int] = 15 * 60  # 15 minutes
REFRESH_TOKEN_TTL_SECONDS: Final[int] = 10 * 24 * 60 * 60  # 10 days

# Security
# TODO: Move to environment variable in production
JWT_SECRET_KEY: Final[str] = "my-random-landman-key-for-jwt-testing"

# Cookie Configuration
REFRESH_TOKEN_COOKIE_NAME: Final[str] = "refresh_token"
REFRESH_TOKEN_COOKIE_PATH: Final[str] = "/"
REFRESH_TOKEN_COOKIE_HTTPONLY: Final[bool] = True
REFRESH_TOKEN_COOKIE_SECURE: Final[bool] = True
REFRESH_TOKEN_COOKIE_SAMESITE: Final[Literal["lax", "strict", "none"]] = "lax"

# Request Headers
SAFE_HEADERS_TO_STORE: Final[set[str]] = {
    "user-agent",
    "referer",
    "accept-language",
    "sec-ch-ua",  # The browser's brand and version information in a structured format.
    "sec-ch-ua-mobile",  # Whether the browser is running on a mobile device.
    "sec-ch-ua-platform",  # The platform the browser is running on.
}
