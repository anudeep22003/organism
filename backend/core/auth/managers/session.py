import uuid
from datetime import timedelta

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.config import REFRESH_TOKEN_TTL_SECONDS
from core.auth.managers.refresh import RefreshTokenManager
from core.auth.models.auth_session import AuthSession
from core.auth.schemas.auth_session import AuthSessionSchema
from core.common.utils import get_current_datetime_utc

logger = logger.bind(__name__)


class SessionManager:
    """Manage authentication sessions."""

    def __init__(
        self, db_session: AsyncSession, refresh_token_manager: RefreshTokenManager
    ) -> None:
        self._db = db_session
        self._refresh_token_manager = refresh_token_manager

    async def create_session(
        self, user_id: uuid.UUID, refresh_token: str
    ) -> AuthSessionSchema:
        now = get_current_datetime_utc()
        expires_at = now + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
        token_hash = self._refresh_token_manager.hash_refresh_token(refresh_token)

        new_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=refresh_token,
            created_at=now,
            expires_at=expires_at,
        )

        self._db.add(new_session)
        await self._db.commit()
        await self._db.refresh(new_session)

        logger.info(f"Created session for user: {user_id}")
        return AuthSessionSchema.model_validate(new_session)

    async def find_session_by_user_id(
        self, user_id: str | uuid.UUID
    ) -> AuthSession | None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        query = select(AuthSession).where(AuthSession.user_id == user_id)
        session = await self._db.scalar(query)
        return session

    async def find_session_by_refresh_token(
        self, refresh_token: str
    ) -> AuthSession | None:
        query = select(AuthSession).where(
            AuthSession.refresh_token_hash
            == self._refresh_token_manager.hash_refresh_token(refresh_token)
        )
        session = await self._db.scalar(query)
        return session

    async def session_is_valid(self, session: AuthSession) -> bool:
        """
        Check if a session is valid (not expired, not revoked).

        Args:
            session: The session to validate

        Returns:
            True if session is valid, False otherwise
        """
        if session.revoked_at is not None:
            return False

        if session.expires_at < get_current_datetime_utc():
            return False

        return True
