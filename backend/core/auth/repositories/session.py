import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuthSession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, session: AuthSession) -> AuthSession:
        self.db.add(session)
        return session

    async def get_session_by_id(self, session_id: uuid.UUID) -> AuthSession | None:
        return await self.db.get(AuthSession, session_id)

    async def update_session(self, session: AuthSession) -> AuthSession:
        return session
