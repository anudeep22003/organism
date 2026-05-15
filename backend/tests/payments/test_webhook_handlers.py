import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models import User
from core.infrastructure.database import configure_psycopg_json_dumps
from core.payments.models import Entitlement, Invoice, StripeCustomer, Subscription
from core.payments.webhooks.handlers import (
    InvoiceWebhookHandler,
    SubscriptionWebhookHandler,
)

configure_psycopg_json_dumps()


def load_stripe_payload(
    fixture_name: str, *, replacements: dict[str, str] | None = None
) -> dict[str, Any]:
    payload_text = Path("stripe_events", fixture_name).read_text()
    for old_value, new_value in (replacements or {}).items():
        payload_text = payload_text.replace(old_value, new_value)
    return cast(dict[str, Any], json.loads(payload_text))


def build_stripe_event(payload: dict) -> stripe.Event:
    return stripe.Event.construct_from(payload, key="sk_test")


def load_stripe_event(
    fixture_name: str, *, replacements: dict[str, str] | None = None
) -> stripe.Event:
    return build_stripe_event(
        load_stripe_payload(fixture_name, replacements=replacements)
    )


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

    handler = SubscriptionWebhookHandler(db_session)
    await handler.handle_created(stripe_event)
    await db_session.commit()

    result = await db_session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == test_ids["created_subscription_id"]
        )
    )
    subscriptions = list(result.scalars().all())

    assert len(subscriptions) == 1
    subscription = subscriptions[0]
    assert subscription.user_id == user.id
    assert subscription.stripe_subscription_id == test_ids["created_subscription_id"]
    assert subscription.stripe_customer_id == test_ids["customer_id"]
    assert subscription.price_id == "price_1TVTbWAMWKJyocPO4ayR6keZ"


@pytest.mark.asyncio
async def test_customer_subscription_updated_handler_updates_subscription(
    db_session: AsyncSession,
    user: User,
) -> None:
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )

    created_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
        },
    )
    handler = SubscriptionWebhookHandler(db_session)
    await handler.handle_created(created_event)
    await db_session.commit()

    updated_payload = load_stripe_payload(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
        },
    )
    updated_payload["type"] = "customer.subscription.updated"
    updated_payload["data"]["object"]["status"] = "past_due"
    updated_payload["data"]["object"]["cancel_at_period_end"] = True
    updated_payload["data"]["object"]["items"]["data"][0]["current_period_end"] = (
        1778751968
    )
    updated_event = build_stripe_event(updated_payload)

    await handler.handle_updated(updated_event)
    await db_session.commit()

    result = await db_session.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == test_ids["created_subscription_id"]
        )
    )
    subscription = result.scalar_one()

    assert subscription.status == "past_due"
    assert subscription.cancel_at_period_end is True
    assert subscription.current_period_end == datetime.fromtimestamp(
        1778751968, tz=timezone.utc
    )


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
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(subscription_event)
    await db_session.commit()

    invoice_event = load_stripe_event(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    invoice_handler = InvoiceWebhookHandler(db_session)
    await invoice_handler.handle_paid(invoice_event)
    await db_session.commit()

    invoice_result = await db_session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == test_ids["invoice_id"])
    )
    invoices = list(invoice_result.scalars().all())
    entitlement_result = await db_session.execute(
        select(Entitlement).where(Entitlement.user_id == user.id)
    )
    entitlements = list(entitlement_result.scalars().all())
    subscription_entitlements = [
        entitlement
        for entitlement in entitlements
        if entitlement.source == "subscription"
    ]

    assert len(invoices) == 1
    assert invoices[0].stripe_invoice_id == test_ids["invoice_id"]
    assert invoices[0].amount_paid == 30000

    assert len(subscription_entitlements) == 1
    assert subscription_entitlements[0].user_id == user.id
    assert subscription_entitlements[0].feature == "pro_tier"
    assert subscription_entitlements[0].source == "subscription"


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
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(subscription_event)
    await db_session.commit()

    invoice_event = load_stripe_event(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    invoice_handler = InvoiceWebhookHandler(db_session)
    await invoice_handler.handle_paid(invoice_event)
    await db_session.commit()
    await invoice_handler.handle_paid(invoice_event)
    await db_session.commit()

    invoice_result = await db_session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == test_ids["invoice_id"])
    )
    entitlement_result = await db_session.execute(
        select(Entitlement).where(Entitlement.user_id == user.id)
    )
    subscription_entitlements = [
        entitlement
        for entitlement in entitlement_result.scalars().all()
        if entitlement.source == "subscription"
    ]

    assert len(list(invoice_result.scalars().all())) == 1
    assert len(subscription_entitlements) == 1


@pytest.mark.asyncio
async def test_invoice_payment_failed_creates_invoice_without_entitlement(
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
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(subscription_event)
    await db_session.commit()

    failed_payload = load_stripe_payload(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    failed_payload["type"] = "invoice.payment_failed"
    failed_payload["data"]["object"]["status"] = "open"
    failed_payload["data"]["object"]["amount_paid"] = 0
    failed_payload["data"]["object"]["status_transitions"]["paid_at"] = None
    failed_event = build_stripe_event(failed_payload)

    invoice_handler = InvoiceWebhookHandler(db_session)
    await invoice_handler.handle_payment_failed(failed_event)
    await db_session.commit()

    invoice_result = await db_session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == test_ids["invoice_id"])
    )
    entitlement_result = await db_session.execute(
        select(Entitlement).where(Entitlement.user_id == user.id)
    )
    invoices = list(invoice_result.scalars().all())
    entitlements = list(entitlement_result.scalars().all())
    subscription_entitlements = [
        entitlement
        for entitlement in entitlements
        if entitlement.source == "subscription"
    ]

    assert len(invoices) == 1
    assert invoices[0].stripe_invoice_id == test_ids["invoice_id"]
    assert invoices[0].status == "open"
    assert invoices[0].amount_paid == 0
    assert len(subscription_entitlements) == 0


@pytest.mark.asyncio
async def test_invoice_paid_after_failed_invoice_creates_entitlement(
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
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(subscription_event)
    await db_session.commit()

    failed_payload = load_stripe_payload(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    failed_payload["type"] = "invoice.payment_failed"
    failed_payload["data"]["object"]["status"] = "open"
    failed_payload["data"]["object"]["amount_paid"] = 0
    failed_payload["data"]["object"]["status_transitions"]["paid_at"] = None
    failed_event = build_stripe_event(failed_payload)

    invoice_handler = InvoiceWebhookHandler(db_session)
    await invoice_handler.handle_payment_failed(failed_event)
    await db_session.commit()

    paid_event = load_stripe_event(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["created_subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    await invoice_handler.handle_paid(paid_event)
    await db_session.commit()

    invoice_result = await db_session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == test_ids["invoice_id"])
    )
    entitlement_result = await db_session.execute(
        select(Entitlement).where(Entitlement.user_id == user.id)
    )
    invoice = invoice_result.scalar_one()
    entitlements = [
        entitlement
        for entitlement in entitlement_result.scalars().all()
        if entitlement.source == "subscription"
    ]

    assert invoice.status == "paid"
    assert invoice.amount_paid == 30000
    assert len(entitlements) == 1
    assert entitlements[0].feature == "pro_tier"
