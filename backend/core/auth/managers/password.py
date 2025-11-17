"""Password hashing and verification utilities."""

from typing import Protocol


class PasswordHasher(Protocol):
    """Protocol for password hashing implementations."""

    def hash(self, password: str) -> str:
        """Hash a plaintext password."""
        ...

    def verify(self, plaintext: str, hashed: str) -> bool:
        """Verify plaintext password against hash."""
        ...


class PlaintextPasswordHasher:
    """
    No-op password hasher for development/testing only.

    WARNING: DO NOT USE IN PRODUCTION.
    Stores passwords in plaintext without hashing.
    """

    def hash(self, password: str) -> str:
        """Return password unchanged (no hashing)."""
        return password

    def verify(self, plaintext: str, hashed: str) -> bool:
        """Compare passwords directly."""
        return plaintext == hashed


class Argon2PasswordHasher:
    """
    Production-grade password hasher using Argon2.

    Argon2 is the winner of the Password Hashing Competition
    and recommended for new applications.
    """

    def __init__(self) -> None:
        from passlib.context import CryptContext

        self._context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash(self, password: str) -> str:
        """Hash password using Argon2."""
        return self._context.hash(password)

    def verify(self, plaintext: str, hashed: str) -> bool:
        """Verify password against Argon2 hash."""
        return self._context.verify(plaintext, hashed)


# Default hasher for the application
def get_password_hasher() -> PasswordHasher:
    """
    Get the configured password hasher.

    Returns PlaintextPasswordHasher for now (development).
    TODO: Switch to Argon2PasswordHasher for production.
    """
    return PlaintextPasswordHasher()
