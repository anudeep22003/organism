import uuid
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from ..exceptions import OAuthProfileFieldError, OAuthUserInfoError
from ..models import GoogleOAuthAccount, User
from ..repositories import AuthRepository
from ..schemas import GoogleOAuthCallbackPayload
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
            raise OAuthUserInfoError("Google OAuth response did not include userinfo")

        payload = self._validate_google_callback_payload(token)

        google_sub = payload.userinfo.sub
        email = payload.userinfo.email
        email_verified = payload.userinfo.email_verified
        name = payload.userinfo.name
        picture_url = payload.userinfo.picture

        access_token = self.token_encryptor.encrypt(payload.access_token)
        refresh_token = self._encrypt_optional_token(payload.refresh_token)
        id_token = self._encrypt_optional_token(payload.id_token)
        scope = payload.scope
        token_expires_at = payload.expires_at

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

    def _encrypt_optional_token(self, value: Any) -> str | None:
        if not isinstance(value, str) or value == "":
            return None
        return self.token_encryptor.encrypt(value)

    def _encrypt_if_plaintext(self, value: str) -> str:
        """Upgrade pre-encryption plaintext token values without double-encrypting."""
        try:
            self.token_encryptor.decrypt(value)
            return value
        except TokenDecryptionError:
            return self.token_encryptor.encrypt(value)

    def _validate_google_callback_payload(
        self, token: dict[str, Any]
    ) -> GoogleOAuthCallbackPayload:
        try:
            return GoogleOAuthCallbackPayload.model_validate(token)
        except ValidationError as exc:
            first_error = exc.errors()[0]
            location = first_error.get("loc", ())
            key = location[-1] if location else "unknown"
            raise OAuthProfileFieldError(
                f"Missing required Google OAuth field: {key}"
            ) from exc
