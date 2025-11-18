"""User account management operations."""

import uuid
from typing import Optional

from fastapi import Request
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import SAFE_HEADERS_TO_STORE
from ..exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from ..managers.password import PasswordHasher, get_password_hasher
from ..models.user import User
from ..schemas.user import UserSchemaCreate, UserSchemaSignin

logger = logger.bind(name=__name__)


class UserManager:
    """Manages user account operations."""

    def __init__(
        self,
        db_session: AsyncSession,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        """
        Initialize user manager.

        Args:
            db_session: Async database session
            password_hasher: Optional custom password hasher
        """
        self._db = db_session
        self._password_hasher = password_hasher or get_password_hasher()

    async def find_user_by_id(self, user_id: uuid.UUID | str) -> Optional[User]:
        if isinstance(user_id, str):
            user_id = uuid.UUID(user_id)

        query = select(User).where(User.id == user_id)
        user = await self._db.scalar(query)
        return user

    async def find_user_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        user = await self._db.scalar(query)
        return user

    async def user_exists_with_email(self, email: str) -> bool:
        user = await self.find_user_by_email(email)
        return user is not None

    def _extract_safe_request_metadata(self, request: Request) -> dict[str, str]:
        return {
            key: value
            for key in SAFE_HEADERS_TO_STORE
            if (value := request.headers.get(key)) is not None
        }

    async def create_user(
        self,
        credentials: UserSchemaCreate,
        request: Request,
    ) -> User:
        """
        Create a new user account.

        Args:
            credentials: User signup credentials
            request: HTTP request for metadata extraction

        Returns:
            The newly created User

        Raises:
            UserAlreadyExistsError: If email already registered
        """
        if await self.user_exists_with_email(credentials.email):
            raise UserAlreadyExistsError(email=credentials.email)

        password_hash = self._password_hasher.hash(credentials.password)
        metadata = self._extract_safe_request_metadata(request)

        new_user = User(
            email=credentials.email,
            password_hash=password_hash,
            meta=metadata,
        )

        self._db.add(new_user)
        await self._db.commit()
        await self._db.refresh(new_user)

        logger.info(f"Created new user: {new_user.email}")
        return new_user

    async def authenticate_user(
        self,
        credentials: UserSchemaSignin,
    ) -> User:
        """
        Authenticate a user with email and password.

        Args:
            credentials: User signin credentials

        Returns:
            The authenticated User

        Raises:
            UserNotFoundError: If email not found
            InvalidCredentialsError: If password incorrect
        """
        user = await self.find_user_by_email(credentials.email)

        if not user:
            logger.debug(f"Authentication failed: user not found - {credentials.email}")
            raise UserNotFoundError(f"User {credentials.email} not found")

        password_valid = self._password_hasher.verify(
            credentials.password,
            user.password_hash,
        )

        if not password_valid:
            logger.debug(
                f"Authentication failed: invalid password - {credentials.email}"
            )
            raise InvalidCredentialsError(
                f"Invalid credentials for user {credentials.email}"
            )

        logger.info(f"User authenticated: {user.email}")
        return user
