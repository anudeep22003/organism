from sqlalchemy.ext.asyncio import AsyncSession

from .google_oauth_account import GoogleOAuthAccountRepository
from .session import SessionRepository
from .user import UserRepository


class AuthRepositoryV2:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user = UserRepository(db)
        self.google_oauth_account = GoogleOAuthAccountRepository(db)
        self.session = SessionRepository(db)


__all__ = [
    "AuthRepositoryV2",
    "GoogleOAuthAccountRepository",
    "SessionRepository",
    "UserRepository",
]
