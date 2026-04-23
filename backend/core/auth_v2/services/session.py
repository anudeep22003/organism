import uuid
from dataclasses import dataclass
from datetime import timedelta

from ..config import REFRESH_TOKEN_TTL_SECONDS
from ..exceptions import InvalidRefreshTokenError
from ..models import AuthSession
from ..repositories import AuthRepository
from ..security import AccessTokenManager, RefreshTokenManager
from ..utils import get_current_datetime_utc


@dataclass(frozen=True, slots=True)
class AuthTokens:
    user_id: uuid.UUID
    access_token: str
    refresh_token: str


class SessionService:
    def __init__(
        self,
        repository: AuthRepository,
        access_token_manager: AccessTokenManager,
        refresh_token_manager: RefreshTokenManager,
    ) -> None:
        self.repository = repository
        self.access_token_manager = access_token_manager
        self.refresh_token_manager = refresh_token_manager

    async def create_app_session(
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
        await self.repository.session.create_session(session)
        access_token = self.access_token_manager.create_access_token(user_id)
        return AuthTokens(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_session(self, refresh_token: str) -> AuthTokens:
        token_parts = self.refresh_token_manager.parse_refresh_token(refresh_token)
        session = await self.repository.session.get_session_by_id(
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
        await self.repository.session.create_session(new_session)
        await self.repository.db.flush()
        session.rotate(new_session.id)
        await self.repository.session.update_session(session)
        return AuthTokens(
            user_id=user_id,
            access_token=self.access_token_manager.create_access_token(user_id),
            refresh_token=new_refresh_token,
        )

    async def logout(self, refresh_token: str | None) -> uuid.UUID | None:
        if refresh_token is None:
            return None
        try:
            token_parts = self.refresh_token_manager.parse_refresh_token(refresh_token)
        except InvalidRefreshTokenError:
            return None

        session = await self.repository.session.get_session_by_id(
            token_parts.session_id
        )
        if session is None:
            return None

        if not self.refresh_token_manager.verify_refresh_token_secret(
            token_parts.secret, session.refresh_token_hash
        ):
            return None

        if session.revoked_at is None:
            session.revoke()
            await self.repository.session.update_session(session)
        return session.user_id
