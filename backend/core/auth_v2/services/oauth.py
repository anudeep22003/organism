import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..models import GoogleOAuthAccount, User
from ..repositories import AuthRepository
from ..security import PasswordHasher, TokenDecryptionError, TokenEncryptor


@dataclass(frozen=True, slots=True)
class CallbackUserResult:
    user_id: uuid.UUID


class OAuthService:
    def __init__(
        self,
        repository: AuthRepository,
        password_hasher: PasswordHasher,
        token_encryptor: TokenEncryptor,
    ) -> None:
        self.repository = repository
        self.password_hasher = password_hasher
        self.token_encryptor = token_encryptor

    async def resolve_google_callback_user(
        self, token: dict[str, Any]
    ) -> CallbackUserResult:
        userinfo = token.get("userinfo")
        if not isinstance(userinfo, dict):
            raise ValueError("Google OAuth response did not include userinfo")

        google_sub = self._require_str(userinfo, "sub")
        email = self._require_str(userinfo, "email")
        email_verified = bool(userinfo.get("email_verified", False))
        name = self._optional_str(userinfo.get("name"))
        picture_url = self._optional_str(userinfo.get("picture"))

        access_token = self.token_encryptor.encrypt(
            self._require_str(token, "access_token")
        )
        refresh_token = self._encrypt_optional_token(token.get("refresh_token"))
        id_token = self._encrypt_optional_token(token.get("id_token"))
        scope = self._optional_str(token.get("scope"))
        token_expires_at = self._parse_token_expires_at(token)

        google_account = (
            await self.repository.google_oauth_account.get_google_oauth_account_by_sub(
                google_sub
            )
        )
        if google_account is not None:
            if google_account.refresh_token is not None and refresh_token is None:
                google_account.refresh_token = self._encrypt_if_plaintext(
                    google_account.refresh_token
                )
            google_account.update_google_login(
                email=email,
                email_verified=email_verified,
                access_token=access_token,
                refresh_token=refresh_token,
                id_token=id_token,
                scope=scope,
                name=name,
                picture_url=picture_url,
                token_expires_at=token_expires_at,
            )
            await self.repository.google_oauth_account.update_google_oauth_account(
                google_account
            )
            return CallbackUserResult(user_id=google_account.user_id)

        user = await self.repository.user.get_user_by_email(email)
        if user is None:
            user = User.create(
                email=email,
                password_hash=self._oauth_only_password_hash(),
            )
            await self.repository.user.create_user(user)
            await self.repository.db.flush()

        google_account = GoogleOAuthAccount.create(
            user_id=user.id,
            google_sub=google_sub,
            email=email,
            email_verified=email_verified,
            access_token=access_token,
            refresh_token=refresh_token,
            id_token=id_token,
            scope=scope,
            name=name,
            picture_url=picture_url,
            token_expires_at=token_expires_at,
        )
        await self.repository.google_oauth_account.create_google_oauth_account(
            google_account
        )
        return CallbackUserResult(user_id=user.id)

    async def get_current_user(self, user_id: uuid.UUID) -> User | None:
        return await self.repository.user.get_user_by_id(user_id)

    def _oauth_only_password_hash(self) -> str:
        import uuid as uuid_module

        return self.password_hasher.hash(f"google-oauth-only:{uuid_module.uuid4()}")

    def _require_str(self, source: dict[str, Any], key: str) -> str:
        value = source.get(key)
        if not isinstance(value, str) or value == "":
            raise ValueError(f"Missing required Google OAuth field: {key}")
        return value

    def _optional_str(self, value: Any) -> str | None:
        if isinstance(value, str) and value != "":
            return value
        return None

    def _encrypt_optional_token(self, value: Any) -> str | None:
        plaintext = self._optional_str(value)
        if plaintext is None:
            return None
        return self.token_encryptor.encrypt(plaintext)

    def _encrypt_if_plaintext(self, value: str) -> str:
        """Upgrade pre-encryption plaintext token values without double-encrypting."""
        try:
            self.token_encryptor.decrypt(value)
            return value
        except TokenDecryptionError:
            return self.token_encryptor.encrypt(value)

    def _parse_token_expires_at(self, token: dict[str, Any]) -> datetime | None:
        expires_at = token.get("expires_at")
        if isinstance(expires_at, (int, float)):
            return datetime.fromtimestamp(expires_at, tz=timezone.utc)
        return None
