"""scope entitlements by livemode

Revision ID: e84a19f68b2d
Revises: c9a0f7a4d6e3
Create Date: 2026-05-29 00:00:03.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e84a19f68b2d"
down_revision: Union[str, Sequence[str], None] = "c9a0f7a4d6e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "entitlement",
        sa.Column(
            "livemode",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.alter_column("entitlement", "livemode", server_default=None)
    op.drop_index("ix_entitlement_user_feature", table_name="entitlement")
    op.drop_index("ix_entitlement_active_lookup", table_name="entitlement")
    op.create_index(
        "ix_entitlement_user_feature",
        "entitlement",
        ["user_id", "feature", "livemode"],
        unique=False,
    )
    op.create_index(
        "ix_entitlement_active_lookup",
        "entitlement",
        ["user_id", "feature", "livemode", "valid_until"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_entitlement_active_lookup", table_name="entitlement")
    op.drop_index("ix_entitlement_user_feature", table_name="entitlement")
    op.create_index(
        "ix_entitlement_active_lookup",
        "entitlement",
        ["user_id", "feature", "valid_until"],
        unique=False,
    )
    op.create_index(
        "ix_entitlement_user_feature",
        "entitlement",
        ["user_id", "feature"],
        unique=False,
    )
    op.drop_column("entitlement", "livemode")
