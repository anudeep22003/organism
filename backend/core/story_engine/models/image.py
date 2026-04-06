from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase
from core.common.utils import get_current_datetime_utc

if TYPE_CHECKING:
    pass


class ImageContentType(StrEnum):
    JPEG = "image/jpeg"
    PNG = "image/png"
    WEBP = "image/webp"


class ImageDiscriminatorKey(StrEnum):
    CHARACTER_REFERENCE = "character_reference"
    CHARACTER_RENDER = "character_render"
    PANEL_RENDER = "panel_render"
    PANEL_REFERENCE = "panel_reference"


class Image(ORMBase):
    __tablename__ = "image"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=get_current_datetime_utc
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # Polymorphic reference — no FK constraint.
    # Application layer enforces referential integrity via discriminator_key.
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False)
    bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    discriminator_key: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    @classmethod
    def create(
        cls,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        target_id: uuid.UUID,
        width: int,
        height: int,
        content_type: ImageContentType,
        object_key: str,
        bucket: str,
        size_bytes: int,
        discriminator_key: ImageDiscriminatorKey,
        meta: dict[str, Any] | None = None,
    ) -> "Image":
        return cls(
            user_id=user_id,
            project_id=project_id,
            target_id=target_id,
            width=width,
            height=height,
            content_type=content_type,
            object_key=object_key,
            bucket=bucket,
            size_bytes=size_bytes,
            discriminator_key=discriminator_key,
            meta=meta or {},
        )
