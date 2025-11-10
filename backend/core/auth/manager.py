import secrets
from abc import ABC, abstractmethod

import jwt
from fastapi import Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.schemas.user import UserResponse, UserSchemaCreate, UserSchemaSignin
from core.sockets.types.envelope import AliasedBaseModel
from core.universe.events import get_current_timestamp

from .models.user import User
from .types import LoginResponse

logger = logger.bind(name=__name__)

ISSUER = "backend-auth-service"
AUDIENCE = "frontend-app"
JWT_ALGORITHM = "HS256"
REFRESH_TOKEN_TTL = 10 * 24 * 60 * 60  # 10 days in seconds
ACCESS_TOKEN_TTL = 15 * 60  # 15 minutes in seconds
SECRET_KEY = "my-random-landman-key-for-jwt-testing"


class PasswordContext(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def verify(self, secret: str, hash: str) -> bool:
        raise NotImplementedError


class SimplePWDContext(PasswordContext):
    def hash(self, password: str) -> str:
        return password

    def verify(self, secret: str, hash: str) -> bool:
        return secret == hash


class JWTPayload(AliasedBaseModel):
    sub: str
    iat: int
    exp: int
    jti: str
    issuer: str
    audience: str


class UserAlreadyExistsException(Exception):
    def __init__(self, email: str) -> None:
        super().__init__(
            f"User {email} already exists in the database. This operation cannot be completed."
        )


class JWTTokensManager:
    def __init__(self) -> None: ...

    def create_access_token(self, user_id: str) -> str:
        iat = get_current_timestamp()
        lifetime = 15 * 60  # 15 minutes in seconds
        exp = iat + lifetime
        jti = secrets.token_urlsafe(32)
        payload = JWTPayload(
            sub=user_id, iat=iat, exp=exp, jti=jti, issuer=ISSUER, audience=AUDIENCE
        )
        return jwt.encode(payload.model_dump(), SECRET_KEY, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self) -> str:
        refresh_token = secrets.token_urlsafe(32)
        return refresh_token

    def refresh_token(self) -> str:
        raise NotImplementedError("Not implemented")

    def verify_access_token(self, token: str) -> bool:
        raise NotImplementedError("Not implemented")

    def verify_refresh_token(self, token: str) -> bool:
        raise NotImplementedError("Not implemented")

    def refresh_access_token(self) -> str:
        raise NotImplementedError("Not implemented")


class SessionManager:
    def __init__(self) -> None: ...

    def create_session(self, user_id: str) -> str:
        raise NotImplementedError("Not implemented")

    def verify_session(self, session_id: str) -> bool:
        raise NotImplementedError("Not implemented")

    def refresh_session(self, session_id: str) -> str:
        raise NotImplementedError("Not implemented")


class AuthManager:
    def __init__(self, async_db_session: AsyncSession) -> None:
        self.async_db_session = async_db_session
        self.password_context = SimplePWDContext()

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

    def create_user(self, email: str, password: str) -> User:
        return User(email=email, password_hash=self.hash_password(password))

    async def create_user_in_db(self, user: User) -> User:
        self.async_db_session.add(user)
        await self.async_db_session.commit()
        await self.async_db_session.refresh(user)
        return user

    async def handle_new_user(
        self, user_request: UserSchemaCreate, request: Request
    ) -> LoginResponse:
        if await self.check_if_user_exists(user_request):
            return LoginResponse(status_code="USER_ALREADY_EXISTS")
        new_user = User(
            email=user_request.email,
            password_hash=self.hash_password(user_request.password),
            meta=self.extract_headers_from_request(request),
        )
        user = await self.create_user_in_db(new_user)
        user_response = UserResponse.model_validate(user)
        return LoginResponse(user=user_response, status_code="SUCCESS")

    async def handle_returning_user(
        self,
        credentials: UserSchemaSignin,
    ) -> LoginResponse:
        existing_user = await self.find_user_by_email(email=credentials.email)
        if not existing_user:
            return LoginResponse(status_code="USER_NOT_FOUND")
        password_match = self.password_context.verify(
            secret=credentials.password, hash=existing_user.password_hash
        )

        if not password_match:
            return LoginResponse(status_code="INVALID_CREDENTIALS")

        return LoginResponse(
            user=UserResponse.model_validate(existing_user), status_code="SUCCESS"
        )
