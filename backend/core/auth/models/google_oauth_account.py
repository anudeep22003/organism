from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.common import ORMBase

from ..utils import get_current_datetime_utc

if TYPE_CHECKING:
    from .user import User


class GoogleOAuthAccount(ORMBase):
    __tablename__ = "google_oauth_account"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    google_sub: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        nullable=False,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
    )

    user: Mapped[User] = relationship("User", back_populates="google_oauth_accounts")

    def __repr__(self) -> str:
        return (
            "GoogleOAuthAccount("
            f"google_sub={self.google_sub}, user_id={self.user_id}, email={self.email}"
            ")"
        )

    @classmethod
    def create(
        cls,
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
    ) -> "GoogleOAuthAccount":
        return cls(
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

    def update_google_login(
        self,
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
    ) -> "GoogleOAuthAccount":
        self.email = email
        self.email_verified = email_verified
        self.access_token = access_token
        if refresh_token is not None:
            self.refresh_token = refresh_token
        self.id_token = id_token
        self.scope = scope
        self.name = name
        self.picture_url = picture_url
        self.token_expires_at = token_expires_at
        self.last_login_at = get_current_datetime_utc()
        self.revoked_at = None
        return self
