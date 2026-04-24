from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.common import ORMBase

from ..utils import get_current_datetime_utc

if TYPE_CHECKING:
    from .google_oauth_account import GoogleOAuthAccount


class User(ORMBase):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=get_current_datetime_utc,
        onupdate=get_current_datetime_utc,
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    google_oauth_accounts: Mapped[list[GoogleOAuthAccount]] = relationship(
        "GoogleOAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(email={self.email}, id={self.id})"

    @classmethod
    def create(
        cls,
        *,
        email: str,
        password_hash: str,
        meta: dict[str, Any] | None = None,
    ) -> "User":
        return cls(
            email=email,
            password_hash=password_hash,
            meta=meta or {},
        )
