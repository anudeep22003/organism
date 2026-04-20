import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase

from ..utils import get_current_datetime_utc


class AuthSession(ORMBase):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE")
    )
    refresh_token_hash: Mapped[str] = mapped_column(String)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    replaced_by_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("session.id"), nullable=True
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
    )

    @classmethod
    def create(
        cls,
        *,
        user_id: uuid.UUID,
        refresh_token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip: str | None = None,
    ) -> "AuthSession":
        return cls(
            id=uuid.uuid4(),
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            user_agent=user_agent,
            ip=ip,
            expires_at=expires_at,
        )

    def rotate(self, replaced_by_session_id: uuid.UUID) -> "AuthSession":
        self.revoked_at = get_current_datetime_utc()
        self.replaced_by_session_id = replaced_by_session_id
        return self

    def revoke(self) -> "AuthSession":
        self.revoked_at = get_current_datetime_utc()
        return self

    def touch(self) -> "AuthSession":
        self.last_used_at = get_current_datetime_utc()
        return self

    def __repr__(self) -> str:
        return f"Session(id={self.id}, user_id={self.user_id}, created_at={self.created_at}, expires_at={self.expires_at}"
