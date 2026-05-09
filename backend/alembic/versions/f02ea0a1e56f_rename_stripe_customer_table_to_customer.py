"""rename stripe_customer table to customer

Revision ID: f02ea0a1e56f
Revises: 15ebf715538f
Create Date: 2026-05-09 17:28:39.362284

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f02ea0a1e56f"
down_revision: Union[str, Sequence[str], None] = "15ebf715538f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.rename_table("stripe_customer", "customer", schema="stripe")
    op.execute(
        "ALTER INDEX stripe.ix_stripe_stripe_customer_user_id "
        "RENAME TO ix_customer_user_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_stripe_customer_stripe_customer_id "
        "RENAME TO ix_customer_stripe_customer_id"
    )

    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_user_id "
        "RENAME TO ix_checkout_session_user_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_stripe_session_id "
        "RENAME TO ix_checkout_session_stripe_session_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_stripe_customer_record_id "
        "RENAME TO ix_checkout_session_stripe_customer_record_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_stripe_customer_id "
        "RENAME TO ix_checkout_session_stripe_customer_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_stripe_payment_intent_id "
        "RENAME TO ix_checkout_session_stripe_payment_intent_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_checkout_session_stripe_subscription_id "
        "RENAME TO ix_checkout_session_stripe_subscription_id"
    )

    op.drop_index("ix_event_type_received_at", table_name="event", schema="stripe")
    op.execute(
        "ALTER INDEX stripe.ix_stripe_event_event_type RENAME TO ix_event_event_type"
    )
    op.execute(
        "ALTER INDEX stripe.ix_stripe_event_stripe_event_id "
        "RENAME TO ix_event_stripe_event_id"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER INDEX stripe.ix_event_stripe_event_id "
        "RENAME TO ix_stripe_event_stripe_event_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_event_event_type RENAME TO ix_stripe_event_event_type"
    )
    op.create_index(
        "ix_event_type_received_at",
        "event",
        ["event_type", "received_at"],
        unique=False,
        schema="stripe",
    )

    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_stripe_subscription_id "
        "RENAME TO ix_stripe_checkout_session_stripe_subscription_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_stripe_payment_intent_id "
        "RENAME TO ix_stripe_checkout_session_stripe_payment_intent_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_stripe_customer_id "
        "RENAME TO ix_stripe_checkout_session_stripe_customer_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_stripe_customer_record_id "
        "RENAME TO ix_stripe_checkout_session_stripe_customer_record_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_stripe_session_id "
        "RENAME TO ix_stripe_checkout_session_stripe_session_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_checkout_session_user_id "
        "RENAME TO ix_stripe_checkout_session_user_id"
    )

    op.execute(
        "ALTER INDEX stripe.ix_customer_stripe_customer_id "
        "RENAME TO ix_stripe_stripe_customer_stripe_customer_id"
    )
    op.execute(
        "ALTER INDEX stripe.ix_customer_user_id "
        "RENAME TO ix_stripe_stripe_customer_user_id"
    )
    op.rename_table("customer", "stripe_customer", schema="stripe")
