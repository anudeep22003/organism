class AuthenticationError(Exception):
    """Base exception for authentication errors"""

    pass


class UserNotFoundError(AuthenticationError):
    """User does not exist"""

    pass


class InvalidCredentialsError(AuthenticationError):
    """Password is incorrect"""

    pass


class UserAlreadyExistsError(AuthenticationError):
    """User with this email already exists"""

    def __init__(self, email: str) -> None:
        super().__init__(
            f"User {email} already exists in the database. This operation cannot be completed."
        )

    pass


class JwtError(Exception):
    """Base exception for JWT errors"""

    pass


class ExpiredTokenError(JwtError):
    """JWT Token expired"""

    pass


class InvalidTokenError(JwtError):
    """Invalid token"""

    pass
