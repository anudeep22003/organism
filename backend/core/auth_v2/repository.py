import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import GoogleOAuthAccount, User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        user: User,
    ) -> User:
        self.db.add(user)
        return user


class GoogleOAuthAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_google_oauth_account_by_sub(
        self, google_sub: str
    ) -> GoogleOAuthAccount | None:
        query = (
            select(GoogleOAuthAccount)
            .where(GoogleOAuthAccount.google_sub == google_sub)
            .options(selectinload(GoogleOAuthAccount.user))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_google_oauth_accounts_for_user(
        self, user_id: uuid.UUID
    ) -> list[GoogleOAuthAccount]:
        query = (
            select(GoogleOAuthAccount)
            .where(GoogleOAuthAccount.user_id == user_id)
            .order_by(GoogleOAuthAccount.created_at.asc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_google_oauth_account(
        self,
        google_oauth_account: GoogleOAuthAccount,
    ) -> GoogleOAuthAccount:
        self.db.add(google_oauth_account)
        return google_oauth_account

    async def update_google_oauth_account(
        self,
        google_oauth_account: GoogleOAuthAccount,
    ) -> GoogleOAuthAccount:
        return google_oauth_account


class AuthRepositoryV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user = UserRepository(db)
        self.google_oauth_account = GoogleOAuthAccountRepository(db)
