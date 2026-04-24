import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import UserNotFoundError
from ..models import User
from ..repositories import AuthRepository
from ..security import (
    AccessTokenManager,
    PasswordHasher,
    RefreshTokenManager,
    TokenEncryptor,
)
from .oauth import OAuthService
from .session import AuthTokens, SessionService


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
        token_encryptor: TokenEncryptor,
    ) -> None:
        self.db = db_session
        self.repository = AuthRepository(db_session)
        self.oauth_service = OAuthService(
            self.repository,
            password_hasher,
            token_encryptor,
        )
        self.session_service = SessionService(
            self.repository,
            access_token_manager,
            refresh_token_manager,
        )

    async def handle_google_callback(
        self,
        token: dict[str, object],
        *,
        user_agent: str | None,
        ip: str | None,
    ) -> CallbackResult:
        callback_user = await self.oauth_service.resolve_google_callback_user(token)
        await self.db.flush()
        tokens = await self.session_service.create_app_session(
            user_id=callback_user.user_id,
            user_agent=user_agent,
            ip=ip,
        )
        await self.db.commit()
        return CallbackResult(user_id=callback_user.user_id, tokens=tokens)

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        user = await self.oauth_service.get_current_user(user_id)
        if user is None:
            raise UserNotFoundError
        return user

    async def refresh_session(self, refresh_token: str) -> AuthTokens:
        tokens = await self.session_service.refresh_session(refresh_token)
        await self.db.flush()
        await self.db.commit()
        return tokens

    async def logout(self, refresh_token: str | None) -> uuid.UUID | None:
        user_id = await self.session_service.logout(refresh_token)
        await self.db.commit()
        return user_id
