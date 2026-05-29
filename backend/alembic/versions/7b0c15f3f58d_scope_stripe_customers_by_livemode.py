"""scope stripe customers by livemode

Revision ID: 7b0c15f3f58d
Revises: 4d6f9e7c2a1b
Create Date: 2026-05-29 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b0c15f3f58d"
down_revision: Union[str, Sequence[str], None] = "4d6f9e7c2a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_index("ix_customer_user_id", table_name="customer", schema="stripe")
    op.create_index(
        "ix_customer_user_livemode",
        "customer",
        ["user_id", "livemode"],
        unique=True,
        schema="stripe",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_customer_user_livemode", table_name="customer", schema="stripe")
    op.create_index(
        "ix_customer_user_id",
        "customer",
        ["user_id"],
        unique=True,
        schema="stripe",
    )
