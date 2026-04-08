"""add name and description to story

Revision ID: e3f9a12b7c41
Revises: 446dd67bbfc8
Create Date: 2026-04-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f9a12b7c41"
down_revision: str | None = "446dd67bbfc8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("story", sa.Column("name", sa.Text(), nullable=True))
    op.add_column("story", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("story", "description")
    op.drop_column("story", "name")
