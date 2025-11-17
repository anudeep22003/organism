import uuid
from datetime import datetime, timedelta, timezone

from fastapi import Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.schemas.user import UserSchemaCreate, UserSchemaSignin

from .config import (
    REFRESH_TOKEN_TTL_SECONDS,
)
from .exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from .managers.password import get_password_hasher
from .models.auth_session import AuthSession
from .models.user import User
from .schemas.auth_session import AuthSessionSchema

logger = logger.bind(name=__name__)


class SessionManager:
    def __init__(self, async_db_session: AsyncSession) -> None:
        self.async_db_session = async_db_session
        self.password_context = get_password_hasher()

    async def create_session(
        self, user_id: uuid.UUID, refresh_token: str
    ) -> AuthSessionSchema:
        created_at = datetime.now(timezone.utc)
        expires_at = created_at + timedelta(seconds=REFRESH_TOKEN_TTL_SECONDS)
        new_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=refresh_token,
            created_at=created_at,
            expires_at=expires_at,
        )

        self.async_db_session.add(new_session)
        await self.async_db_session.commit()
        await self.async_db_session.refresh(new_session)
        return AuthSessionSchema.model_validate(new_session)

    async def find_session_by_user_id(self, user_id: str) -> AuthSession | None:
        select_session_query = select(AuthSession).where(
            AuthSession.user_id == uuid.UUID(user_id)
        )
        session = await self.async_db_session.scalar(select_session_query)
        return session

    async def find_session_by_refresh_token(
        self, refresh_token: str
    ) -> AuthSession | None:
        select_session_query = select(AuthSession).where(
            AuthSession.refresh_token_hash == self.password_context.hash(refresh_token)
        )
        session = await self.async_db_session.scalar(select_session_query)
        return session

    def verify_session(self, session_id: str) -> bool:
        raise NotImplementedError("Not implemented")

    def refresh_session(self, session_id: str) -> str:
        raise NotImplementedError("Not implemented")


class AuthManager:
    def __init__(self, async_db_session: AsyncSession) -> None:
        self.async_db_session = async_db_session
        self.password_context = get_password_hasher()

    async def find_user_by_email(self, email: str) -> User | None:
        select_user_query = select(User).where(User.email == email)
        user = await self.async_db_session.scalar(select_user_query)
        return user

    async def check_if_user_exists(self, user_request: UserSchemaCreate) -> bool:
        email = user_request.email
        user = await self.find_user_by_email(email)
        if user is None:
            logger.debug("No user found.")
            return False
        logger.debug("user found", user=user)
        return True

    def hash_password(self, password: str) -> str:
        return self.password_context.hash(password)

    def extract_headers_from_request(self, request: Request) -> dict:
        return dict(request.headers)

    async def create_user_in_db(self, user: User) -> User:
        self.async_db_session.add(user)
        await self.async_db_session.commit()
        await self.async_db_session.refresh(user)
        return user

    async def create_new_user(
        self, credentials: UserSchemaCreate, request: Request
    ) -> User:
        """Create a new user. Raise UserAlreadyExists Exception if user already exists."""
        if await self.check_if_user_exists(credentials):
            raise UserAlreadyExistsError(email=credentials.email)

        new_user = User(
            email=credentials.email,
            password_hash=self.hash_password(credentials.password),
            meta=self.extract_headers_from_request(request),
        )
        return await self.create_user_in_db(new_user)

    async def authenticate_user(self, credentials: UserSchemaSignin) -> User:
        user = await self.find_user_by_email(email=credentials.email)
        if not user:
            raise UserNotFoundError(f"User {credentials.email} not found")
        password_match = self.password_context.verify(
            plaintext=credentials.password, hashed=user.password_hash
        )
        if not password_match:
            raise InvalidCredentialsError(
                f"Invalid credentials for user {credentials.email}"
            )
        return user
