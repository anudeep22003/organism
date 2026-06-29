"""add livemode to stripe mirrors

Revision ID: 4d6f9e7c2a1b
Revises: 79ef6688c75d
Create Date: 2026-05-29 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d6f9e7c2a1b"
down_revision: Union[str, Sequence[str], None] = "79ef6688c75d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    for table_name in ("event", "checkout_session", "subscription", "invoice"):
        op.add_column(
            table_name,
            sa.Column(
                "livemode",
                sa.Boolean(),
                server_default=sa.false(),
                nullable=False,
            ),
            schema="stripe",
        )
        op.alter_column(
            table_name,
            "livemode",
            server_default=None,
            schema="stripe",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table_name in ("invoice", "subscription", "checkout_session", "event"):
        op.drop_column(table_name, "livemode", schema="stripe")
