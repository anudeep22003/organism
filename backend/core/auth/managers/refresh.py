import secrets

from .password import PasswordHasher, get_password_hasher


class RefreshTokenManager:
    """Manages refresh token generation and verification."""

    def __init__(self, password_hasher: PasswordHasher | None = None) -> None:
        """Initialize the RefreshTokenManager.

        Args:
            password_hasher: The password hasher to use. If None, a default hasher will be used.
        """
        self._password_hasher = password_hasher or get_password_hasher()

    def create_refresh_token(self) -> str:
        """
        Generate a cryptographically secure random refresh token.

        Returns:
            URL-safe base64 encoded refresh token.
        """
        return secrets.token_urlsafe(32)

    def hash_refresh_token(self, refresh_token: str) -> str:
        """
        Hash a refresh token using the configured password hasher.

        Args:
            refresh_token: The refresh token to hash.

        Returns:
            Hashed refresh token suitable for storage in the database.
        """
        return self._password_hasher.hash(refresh_token)

    def verify_refresh_token(
        self, refresh_token: str, hashed_refresh_token: str
    ) -> bool:
        """
        Verify a refresh token against a stored hashed refresh token.

        Args:
            refresh_token: The plaintext refresh token to verify.
            hashed_refresh_token: The stored hashed refresh token to verify against.

        Returns:
            True if the refresh token is valid, False otherwise.
        """
        return self._password_hasher.verify(
            plaintext=refresh_token, hashed=hashed_refresh_token
        )
