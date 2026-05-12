import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User
from core.infrastructure.database import configure_psycopg_json_dumps
from core.payments.models import Entitlement, Invoice, StripeCustomer, Subscription
from core.payments.webhooks.handlers import (
    CustomerSubscriptionCreatedHandler,
    InvoicePaidHandler,
)

configure_psycopg_json_dumps()


def load_stripe_event(
    fixture_name: str, *, replacements: dict[str, str] | None = None
) -> stripe.Event:
    payload_text = Path("stripe_events", fixture_name).read_text()
    for old_value, new_value in (replacements or {}).items():
        payload_text = payload_text.replace(old_value, new_value)
    payload = json.loads(payload_text)
    return stripe.Event.construct_from(payload, key="sk_test")


def make_test_stripe_ids() -> dict[str, str]:
    suffix = uuid.uuid4().hex[:14]
    return {
        "customer_id": f"cus_test_{suffix}",
        "created_subscription_id": f"sub_created_{suffix}",
        "deleted_subscription_id": f"sub_deleted_{suffix}",
        "invoice_id": f"in_test_{suffix}",
    }


async def seed_stripe_customer(
    db_session: AsyncSession, user: User, *, stripe_customer_id: str
) -> StripeCustomer:
    stripe_customer = StripeCustomer.create(
        user_id=user.id,
        stripe_customer_id=stripe_customer_id,
        stripe_created_at=datetime.now(timezone.utc),
        livemode=False,
        raw_stripe_object={"id": stripe_customer_id, "object": "customer"},
        stripe_object="customer",
    )
    db_session.add(stripe_customer)
    await db_session.commit()
    await db_session.refresh(stripe_customer)
    return stripe_customer


@pytest.mark.asyncio
async def test_customer_subscription_created_handler_creates_subscription(
    db_session: AsyncSession,
    user: User,
) -> None:
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )
    stripe_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
        },
    )

    handler = CustomerSubscriptionCreatedHandler(db_session)
    await handler.handle(stripe_event)
    await db_session.commit()

    result = await db_session.execute(select(Subscription))
    subscriptions = list(result.scalars().all())

    assert len(subscriptions) == 1
    subscription = subscriptions[0]
    assert subscription.user_id == user.id
    assert subscription.stripe_subscription_id == test_ids["created_subscription_id"]
    assert subscription.stripe_customer_id == test_ids["customer_id"]
    assert subscription.price_id == "price_1TVTbWAMWKJyocPO4ayR6keZ"


@pytest.mark.asyncio
async def test_invoice_paid_handler_creates_invoice_and_entitlement(
    db_session: AsyncSession,
    user: User,
) -> None:
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )

    subscription_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
        },
    )
    subscription_handler = CustomerSubscriptionCreatedHandler(db_session)
    await subscription_handler.handle(subscription_event)
    await db_session.commit()

    invoice_event = load_stripe_event(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    invoice_handler = InvoicePaidHandler(db_session)
    await invoice_handler.handle(invoice_event)
    await db_session.commit()

    invoice_result = await db_session.execute(select(Invoice))
    invoices = list(invoice_result.scalars().all())
    entitlement_result = await db_session.execute(select(Entitlement))
    entitlements = list(entitlement_result.scalars().all())

    assert len(invoices) == 1
    assert invoices[0].stripe_invoice_id == test_ids["invoice_id"]
    assert invoices[0].amount_paid == 30000

    assert len(entitlements) == 1
    assert entitlements[0].user_id == user.id
    assert entitlements[0].feature == "pro_tier"
    assert entitlements[0].source == "subscription"


@pytest.mark.asyncio
async def test_invoice_paid_handler_is_idempotent_for_same_invoice(
    db_session: AsyncSession,
    user: User,
) -> None:
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )

    subscription_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
        },
    )
    subscription_handler = CustomerSubscriptionCreatedHandler(db_session)
    await subscription_handler.handle(subscription_event)
    await db_session.commit()

    invoice_event = load_stripe_event(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    invoice_handler = InvoicePaidHandler(db_session)
    await invoice_handler.handle(invoice_event)
    await db_session.commit()
    await invoice_handler.handle(invoice_event)
    await db_session.commit()

    invoice_result = await db_session.execute(select(Invoice))
    entitlement_result = await db_session.execute(select(Entitlement))

    assert len(list(invoice_result.scalars().all())) == 1
    assert len(list(entitlement_result.scalars().all())) == 1
