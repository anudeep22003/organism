import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from .models import GoogleOAuthAccount, User
from .repository import AuthRepositoryV2


class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repository_v2 = AuthRepositoryV2(db_session)

    async def handle_google_callback(self, token: dict[str, Any]) -> uuid.UUID:
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
            await self.db.commit()
            return user_id

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
        await self.db.commit()
        return user_id

    def _oauth_only_password_hash(self) -> str:
        return f"google-oauth-only:{secrets.token_urlsafe(32)}"

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
