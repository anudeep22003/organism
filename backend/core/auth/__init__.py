from .dependencies import get_current_user_id, get_user_manager
from .exceptions import (
    AuthenticationError,
    ExpiredTokenError,
    InvalidCredentialsError,
    InvalidTokenError,
    JwtError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .managers import JWTTokenManager, RefreshTokenManager, SessionManager, UserManager
from .router import router as auth_router

__all__ = [
    # Router
    "auth_router",
    # Managers
    "JWTTokenManager",
    "RefreshTokenManager",
    "SessionManager",
    "UserManager",
    # Dependencies (for use in other routers)
    "get_current_user_id",
    "get_user_manager",
    # Password utilities
    "PasswordHasher",
    "get_password_hasher",
    # Models
    "JWTPayload",
    # Exceptions
    "AuthenticationError",
    "UserNotFoundError",
    "InvalidCredentialsError",
    "UserAlreadyExistsError",
    "JwtError",
    "ExpiredTokenError",
    "InvalidTokenError",
]
