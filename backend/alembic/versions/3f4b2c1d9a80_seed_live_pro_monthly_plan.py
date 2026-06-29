"""seed live pro monthly plan

Revision ID: 3f4b2c1d9a80
Revises: e84a19f68b2d
Create Date: 2026-06-29 00:00:00.000000

"""

from typing import Sequence, Union
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f4b2c1d9a80"
down_revision: Union[str, Sequence[str], None] = "e84a19f68b2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PLAN_ID = "pro_monthly"
LIVE_STRIPE_PRICE_ID = "price_1Tnfp5AF0eTxrB9NN5JOVAuJ"


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        sa.text(
            """
            INSERT INTO plan (
                id,
                plan_id,
                display_name,
                description,
                stripe_price_id,
                livemode,
                entitlement_feature,
                features,
                amount_minor,
                currency,
                interval,
                is_active,
                sort_order,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :plan_id,
                'Pro',
                'For creators making stories regularly.',
                :stripe_price_id,
                true,
                'pro_tier',
                CAST(:features AS jsonb),
                2500,
                'usd',
                'month',
                true,
                10,
                now(),
                now()
            )
            ON CONFLICT (plan_id, livemode) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                stripe_price_id = EXCLUDED.stripe_price_id,
                entitlement_feature = EXCLUDED.entitlement_feature,
                features = EXCLUDED.features,
                amount_minor = EXCLUDED.amount_minor,
                currency = EXCLUDED.currency,
                interval = EXCLUDED.interval,
                is_active = EXCLUDED.is_active,
                sort_order = EXCLUDED.sort_order,
                updated_at = now()
            """
        ).bindparams(
            sa.bindparam("id", value=uuid4(), type_=postgresql.UUID(as_uuid=True)),
            plan_id=PLAN_ID,
            stripe_price_id=LIVE_STRIPE_PRICE_ID,
            features=(
                '[{"label":"Generate stories"},'
                '{"label":"Create characters and panels"},'
                '{"label":"Export comics"}]'
            ),
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        sa.text(
            """
            DELETE FROM plan
            WHERE plan_id = :plan_id
              AND livemode IS true
              AND stripe_price_id = :stripe_price_id
            """
        ).bindparams(
            plan_id=PLAN_ID,
            stripe_price_id=LIVE_STRIPE_PRICE_ID,
        )
    )
