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

logger = logger.bind(name=__name__)


class SessionManager:
    """Manage authentication sessions."""

    def __init__(
        self,
        db_session: AsyncSession,
        refresh_token_manager: RefreshTokenManager | None = None,
    ) -> None:
        self._db = db_session
        self._refresh_token_manager = refresh_token_manager or RefreshTokenManager()

    async def create_session(
        self,
        user_id: uuid.UUID,
        refresh_token: str,
        user_agent: str | None,
        ip: str | None,
    ) -> AuthSessionSchema:
        now = get_current_datetime_utc()
        expires_at = now + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
        token_hash = self._refresh_token_manager.hash_refresh_token(refresh_token)

        new_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=token_hash,
            user_agent=user_agent,
            ip=ip,
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

    async def find_best_matching_session(
        self, user_id: str | uuid.UUID, ip: str | None, user_agent: str | None
    ) -> AuthSession | None:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        # Priority 1: Match user_id, ip AND user_agent
        query = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.ip == ip,
            AuthSession.user_agent == user_agent,
        )
        session = await self._db.scalar(query)
        if session:
            return session

        # Priority 2: Match user_id AND ip
        query = select(AuthSession).where(
            AuthSession.user_id == user_id,
            AuthSession.ip == ip,
        )
        session = await self._db.scalar(query)
        if session:
            return session  # type: ignore[no-any-return]

        # Priority 3: Match user_id only
        query = select(AuthSession).where(AuthSession.user_id == user_id)
        session = await self._db.scalar(query)

        return session  # type: ignore[no-any-return]

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

    async def refresh_session(
        self, session: AuthSession, new_refresh_token: str
    ) -> AuthSessionSchema:
        # extract values before they will be used
        user_id = session.user_id
        user_agent = session.user_agent
        ip = session.ip
        logger.info(
            f"Refreshing session for user: {user_id}, ip: {ip}, user_agent: {user_agent}"
        )

        # revoke the old session
        session.revoked_at = get_current_datetime_utc()

        # hash the new refresh token
        new_token_hash = self._refresh_token_manager.hash_refresh_token(
            new_refresh_token
        )

        # create new session with new refresh token hash
        new_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=new_token_hash,
            user_agent=user_agent,
            ip=ip,
            created_at=get_current_datetime_utc(),
            expires_at=get_current_datetime_utc()
            + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS),
        )
        # add the new session to the database (old session is already tracked)
        self._db.add(new_session)

        # commit both in a single transaction
        await self._db.commit()

        # refresh the new session
        await self._db.refresh(new_session)

        # return the new session
        return AuthSessionSchema.model_validate(new_session)
