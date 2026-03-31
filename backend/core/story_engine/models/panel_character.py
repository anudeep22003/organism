from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from core.common import ORMBase


class PanelCharacter(ORMBase):
    """Join table linking panels to the characters who appear in them."""

    __tablename__ = "panel_character"
    __table_args__ = (PrimaryKeyConstraint("panel_id", "character_id"),)

    panel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("panel.id", ondelete="CASCADE"),
        nullable=False,
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("character.id", ondelete="CASCADE"),
        nullable=False,
    )
