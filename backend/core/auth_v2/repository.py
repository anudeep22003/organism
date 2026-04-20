import uuid
from datetime import datetime
from typing import Any

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
        *,
        email: str,
        password_hash: str,
        meta: dict[str, Any] | None = None,
    ) -> User:
        user = User(email=email, password_hash=password_hash, meta=meta or {})
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
        *,
        user_id: uuid.UUID,
        google_sub: str,
        email: str,
        email_verified: bool,
        access_token: str,
        refresh_token: str | None = None,
        id_token: str | None = None,
        scope: str | None = None,
        name: str | None = None,
        picture_url: str | None = None,
        token_expires_at: datetime | None = None,
    ) -> GoogleOAuthAccount:
        google_oauth_account = GoogleOAuthAccount(
            user_id=user_id,
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
        self.db.add(google_oauth_account)
        return google_oauth_account

    async def update_google_oauth_account(
        self,
        google_oauth_account: GoogleOAuthAccount,
        *,
        email: str,
        email_verified: bool,
        access_token: str,
        refresh_token: str | None,
        id_token: str | None,
        scope: str | None,
        name: str | None,
        picture_url: str | None,
        token_expires_at: datetime | None,
    ) -> GoogleOAuthAccount:
        google_oauth_account.email = email
        google_oauth_account.email_verified = email_verified
        google_oauth_account.access_token = access_token
        google_oauth_account.refresh_token = refresh_token
        google_oauth_account.id_token = id_token
        google_oauth_account.scope = scope
        google_oauth_account.name = name
        google_oauth_account.picture_url = picture_url
        google_oauth_account.token_expires_at = token_expires_at
        google_oauth_account.revoked_at = None
        return google_oauth_account


class AuthRepositoryV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user = UserRepository(db)
        self.google_oauth_account = GoogleOAuthAccountRepository(db)
