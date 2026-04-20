from sqlalchemy.ext.asyncio import AsyncSession

from .repository import AuthRepositoryV2


class AuthService:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.repository_v2 = AuthRepositoryV2(db_session)
