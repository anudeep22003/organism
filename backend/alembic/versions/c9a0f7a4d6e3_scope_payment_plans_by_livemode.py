"""scope payment plans by livemode

Revision ID: c9a0f7a4d6e3
Revises: 7b0c15f3f58d
Create Date: 2026-05-29 00:00:02.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c9a0f7a4d6e3"
down_revision: Union[str, Sequence[str], None] = "7b0c15f3f58d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "plan",
        sa.Column(
            "livemode",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.alter_column("plan", "livemode", server_default=None)
    op.drop_index("ix_plan_plan_id", table_name="plan")
    op.drop_index("ix_plan_active_sort_order", table_name="plan")
    op.create_index(
        "ix_plan_plan_id_livemode",
        "plan",
        ["plan_id", "livemode"],
        unique=True,
    )
    op.create_index(
        "ix_plan_active_sort_order",
        "plan",
        ["livemode", "is_active", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_plan_active_sort_order", table_name="plan")
    op.drop_index("ix_plan_plan_id_livemode", table_name="plan")
    op.create_index("ix_plan_active_sort_order", "plan", ["is_active", "sort_order"])
    op.create_index("ix_plan_plan_id", "plan", ["plan_id"], unique=True)
    op.drop_column("plan", "livemode")
