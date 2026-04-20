import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .config import REFRESH_TOKEN_TTL_SECONDS
from .exceptions import InvalidRefreshTokenError, UserNotFoundError
from .hashers import PasswordHasher
from .models import AuthSession, GoogleOAuthAccount, User
from .repository import AuthRepositoryV2
from .tokens import AccessTokenManager, RefreshTokenManager
from .utils import get_current_datetime_utc


@dataclass(frozen=True, slots=True)
class AuthTokens:
    access_token: str
    refresh_token: str


@dataclass(frozen=True, slots=True)
class CallbackResult:
    user_id: uuid.UUID
    tokens: AuthTokens


class AuthService:
    def __init__(
        self,
        db_session: AsyncSession,
        access_token_manager: AccessTokenManager,
        refresh_token_manager: RefreshTokenManager,
        password_hasher: PasswordHasher,
    ):
        self.db = db_session
        self.repository_v2 = AuthRepositoryV2(db_session)
        self.access_token_manager = access_token_manager
        self.refresh_token_manager = refresh_token_manager
        self.password_hasher = password_hasher

    async def handle_google_callback(
        self,
        token: dict[str, Any],
        *,
        user_agent: str | None,
        ip: str | None,
    ) -> CallbackResult:
        userinfo = token.get("userinfo")
        if not isinstance(userinfo, dict):
            raise ValueError("Google OAuth response did not include userinfo")

        google_sub = self._require_str(userinfo, "sub")
        email = self._require_str(userinfo, "email")
        email_verified = bool(userinfo.get("email_verified", False))
        name = self._optional_str(userinfo.get("name"))
        picture_url = self._optional_str(userinfo.get("picture"))

        access_token = self._require_str(token, "access_token")
        refresh_token = self._optional_str(token.get("refresh_token"))
        id_token = self._optional_str(token.get("id_token"))
        scope = self._optional_str(token.get("scope"))
        token_expires_at = self._parse_token_expires_at(token)

        google_account = await self.repository_v2.google_oauth_account.get_google_oauth_account_by_sub(
            google_sub
        )
        if google_account is not None:
            user_id = google_account.user_id
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
            await self.repository_v2.google_oauth_account.update_google_oauth_account(
                google_account
            )
            tokens = await self._create_app_session(
                user_id=user_id,
                user_agent=user_agent,
                ip=ip,
            )
            await self.db.commit()
            return CallbackResult(user_id=user_id, tokens=tokens)

        user = await self.repository_v2.user.get_user_by_email(email)
        if user is None:
            user = User.create(
                email=email,
                password_hash=self._oauth_only_password_hash(),
            )
            await self.repository_v2.user.create_user(user)
            await self.db.flush()

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
        await self.repository_v2.google_oauth_account.create_google_oauth_account(
            google_account
        )
        user_id = user.id
        tokens = await self._create_app_session(
            user_id=user_id,
            user_agent=user_agent,
            ip=ip,
        )
        await self.db.commit()
        return CallbackResult(user_id=user_id, tokens=tokens)

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        user = await self.repository_v2.user.get_user_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        return user

    async def refresh_session(self, refresh_token: str) -> AuthTokens:
        token_parts = self.refresh_token_manager.parse_refresh_token(refresh_token)
        session = await self.repository_v2.session.get_session_by_id(
            token_parts.session_id
        )
        if session is None:
            raise InvalidRefreshTokenError("Refresh session not found")

        if not self.refresh_token_manager.verify_refresh_token_secret(
            token_parts.secret, session.refresh_token_hash
        ):
            raise InvalidRefreshTokenError("Invalid refresh token")

        if session.revoked_at is not None:
            raise InvalidRefreshTokenError("Refresh session revoked")

        if session.expires_at < get_current_datetime_utc():
            raise InvalidRefreshTokenError("Refresh session expired")

        user_id = session.user_id
        new_session = AuthSession.create(
            user_id=user_id,
            refresh_token_hash="",
            expires_at=get_current_datetime_utc()
            + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS),
            user_agent=session.user_agent,
            ip=session.ip,
        )
        new_refresh_token, new_secret_hash = (
            self.refresh_token_manager.create_refresh_token(new_session.id)
        )
        new_session.refresh_token_hash = new_secret_hash
        new_session.touch()
        await self.repository_v2.session.create_session(new_session)
        await self.db.flush()
        session.rotate(new_session.id)
        await self.repository_v2.session.update_session(session)
        await self.db.commit()
        return AuthTokens(
            access_token=self.access_token_manager.create_access_token(user_id),
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return
        try:
            token_parts = self.refresh_token_manager.parse_refresh_token(refresh_token)
        except InvalidRefreshTokenError:
            return

        session = await self.repository_v2.session.get_session_by_id(
            token_parts.session_id
        )
        if session is None:
            return

        if not self.refresh_token_manager.verify_refresh_token_secret(
            token_parts.secret, session.refresh_token_hash
        ):
            return

        if session.revoked_at is None:
            session.revoke()
            await self.repository_v2.session.update_session(session)
            await self.db.commit()

    async def _create_app_session(
        self,
        *,
        user_id: uuid.UUID,
        user_agent: str | None,
        ip: str | None,
    ) -> AuthTokens:
        session = AuthSession.create(
            user_id=user_id,
            refresh_token_hash="",
            expires_at=get_current_datetime_utc()
            + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS),
            user_agent=user_agent,
            ip=ip,
        )
        refresh_token, refresh_token_hash = (
            self.refresh_token_manager.create_refresh_token(session.id)
        )
        session.refresh_token_hash = refresh_token_hash
        session.touch()
        await self.repository_v2.session.create_session(session)
        access_token = self.access_token_manager.create_access_token(user_id)
        return AuthTokens(access_token=access_token, refresh_token=refresh_token)

    def _oauth_only_password_hash(self) -> str:
        return self.password_hasher.hash(f"google-oauth-only:{uuid.uuid4()}")

    def _require_str(self, source: dict[str, Any], key: str) -> str:
        value = source.get(key)
        if not isinstance(value, str) or value == "":
            raise ValueError(f"Missing required Google OAuth field: {key}")
        return value

    def _optional_str(self, value: Any) -> str | None:
        if isinstance(value, str) and value != "":
            return value
        return None

    def _parse_token_expires_at(self, token: dict[str, Any]) -> datetime | None:
        expires_at = token.get("expires_at")
        if isinstance(expires_at, (int, float)):
            return datetime.fromtimestamp(expires_at, tz=timezone.utc)
        return None
