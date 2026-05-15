import json
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
import stripe
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.auth.models import User
from core.config import settings
from core.infrastructure.database import configure_psycopg_json_dumps
from core.payments.models import (
    Entitlement,
    Invoice,
    StripeCustomer,
    StripeEvent,
    StripeEventProcessingStatus,
)
from core.payments.webhooks import (
    StripeEventDrainer,
    StripeEventProcessor,
)
from core.payments.webhooks.exceptions import (
    NonRetryableStripeWebhookError,
    RetryableStripeWebhookError,
)
from core.payments.webhooks.handlers import SubscriptionWebhookHandler

configure_psycopg_json_dumps()


def load_stripe_payload(
    fixture_name: str, *, replacements: dict[str, str] | None = None
) -> dict[str, Any]:
    payload_text = Path("stripe_events", fixture_name).read_text()
    for old_value, new_value in (replacements or {}).items():
        payload_text = payload_text.replace(old_value, new_value)
    return cast(dict[str, Any], json.loads(payload_text))


def build_stripe_event(payload: dict[str, Any]) -> stripe.Event:
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
        "event_id": f"evt_test_{suffix}",
        "customer_id": f"cus_test_{suffix}",
        "subscription_id": f"sub_test_{suffix}",
        "other_subscription_id": f"sub_other_{suffix}",
        "invoice_id": f"in_test_{suffix}",
    }


@pytest_asyncio.fixture
async def stripe_event_cleanup_ids() -> AsyncGenerator[list[uuid.UUID], None]:
    ids: list[uuid.UUID] = []
    yield ids

    teardown_engine = create_async_engine(settings.database_url, echo=False)
    try:
        async with async_sessionmaker(teardown_engine)() as teardown_session:
            if ids:
                await teardown_session.execute(
                    delete(StripeEvent).where(StripeEvent.id.in_(ids))
                )
                await teardown_session.commit()
    finally:
        await teardown_engine.dispose()


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
async def test_drainer_replays_retryable_invoice_event_after_subscription_create(
    db_session: AsyncSession,
    user: User,
    stripe_event_cleanup_ids: list[uuid.UUID],
) -> None:
    user_id = user.id
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )

    invoice_payload = load_stripe_payload(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    invoice_payload["id"] = test_ids["event_id"]
    invoice_event = build_stripe_event(invoice_payload)
    persisted_event = StripeEvent.create(stripe_event=invoice_event)
    db_session.add(persisted_event)
    await db_session.commit()
    stripe_event_cleanup_ids.append(persisted_event.id)

    processor = StripeEventProcessor(db_session)
    with pytest.raises(RetryableStripeWebhookError):
        await processor.process(stripe_event=persisted_event)
    await db_session.refresh(user)

    failed_event = await db_session.get(StripeEvent, persisted_event.id)
    assert failed_event is not None
    assert (
        failed_event.processing_status
        == StripeEventProcessingStatus.RETRYABLE_FAILED.value
    )
    assert failed_event.attempt_count == 1
    assert failed_event.processing_error == (
        f"Subscription {test_ids['subscription_id']} not found locally"
    )

    subscription_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["subscription_id"],
        },
    )
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(subscription_event)
    await db_session.commit()

    drainer = StripeEventDrainer()
    summary = await drainer.drain(limit=50)
    await db_session.refresh(persisted_event)

    assert summary.scanned >= 1
    assert summary.processed >= 1

    invoice_result = await db_session.execute(
        select(Invoice).where(Invoice.stripe_invoice_id == test_ids["invoice_id"])
    )
    entitlement_result = await db_session.execute(
        select(Entitlement).where(Entitlement.user_id == user_id)
    )

    assert invoice_result.scalar_one().stripe_invoice_id == test_ids["invoice_id"]
    entitlements = list(entitlement_result.scalars().all())
    assert len(entitlements) == 2
    assert any(entitlement.source == "subscription" for entitlement in entitlements)
    assert (
        persisted_event.processing_status == StripeEventProcessingStatus.PROCESSED.value
    )
    assert persisted_event.processing_error is None
    assert persisted_event.attempt_count == 2


@pytest.mark.asyncio
async def test_drainer_processes_pending_unsupported_event(
    db_session: AsyncSession,
    stripe_event_cleanup_ids: list[uuid.UUID],
) -> None:
    test_ids = make_test_stripe_ids()
    unsupported_payload = load_stripe_payload(
        "invoice.paid.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["subscription_id"],
            "in_1TVTwWAMWKJyocPOIWrUSKfg": test_ids["invoice_id"],
        },
    )
    unsupported_payload["id"] = test_ids["event_id"]
    unsupported_payload["type"] = "invoice.finalization_failed"
    unsupported_event = build_stripe_event(unsupported_payload)

    persisted_event = StripeEvent.create(stripe_event=unsupported_event)
    db_session.add(persisted_event)
    await db_session.commit()
    stripe_event_cleanup_ids.append(persisted_event.id)

    drainer = StripeEventDrainer()
    summary = await drainer.drain(limit=50)
    await db_session.refresh(persisted_event)
    refreshed_event = await db_session.get(StripeEvent, persisted_event.id)

    assert summary.scanned >= 1
    assert summary.processed >= 1
    assert refreshed_event is not None
    assert (
        refreshed_event.processing_status == StripeEventProcessingStatus.PROCESSED.value
    )
    assert refreshed_event.attempt_count == 1


@pytest.mark.asyncio
async def test_terminal_failed_event_is_not_drainable(
    db_session: AsyncSession,
    user: User,
    stripe_event_cleanup_ids: list[uuid.UUID],
) -> None:
    _ = user.id
    test_ids = make_test_stripe_ids()
    await seed_stripe_customer(
        db_session, user, stripe_customer_id=test_ids["customer_id"]
    )

    initial_subscription_event = load_stripe_event(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["subscription_id"],
        },
    )
    subscription_handler = SubscriptionWebhookHandler(db_session)
    await subscription_handler.handle_created(initial_subscription_event)
    await db_session.commit()

    conflicting_subscription_payload = load_stripe_payload(
        "customer.subscription.created.json",
        replacements={
            "cus_UUDE8Rr8Qy9ZZe": test_ids["customer_id"],
            "sub_1TVTwYAMWKJyocPOpydP2qtC": test_ids["other_subscription_id"],
        },
    )
    conflicting_subscription_payload["id"] = test_ids["event_id"]
    conflicting_subscription_event = build_stripe_event(
        conflicting_subscription_payload
    )
    persisted_event = StripeEvent.create(stripe_event=conflicting_subscription_event)
    db_session.add(persisted_event)
    await db_session.commit()
    stripe_event_cleanup_ids.append(persisted_event.id)

    processor = StripeEventProcessor(db_session)
    with pytest.raises(NonRetryableStripeWebhookError):
        await processor.process(stripe_event=persisted_event)
    await db_session.refresh(user)

    failed_event = await db_session.get(StripeEvent, persisted_event.id)
    assert failed_event is not None
    assert (
        failed_event.processing_status
        == StripeEventProcessingStatus.TERMINAL_FAILED.value
    )

    drainer = StripeEventDrainer()
    summary = await drainer.drain(limit=50)
    drainable_events = await db_session.execute(
        select(StripeEvent).where(
            StripeEvent.processing_status.in_(
                [
                    StripeEventProcessingStatus.PENDING.value,
                    StripeEventProcessingStatus.RETRYABLE_FAILED.value,
                ]
            )
        )
    )
    drainable_event_ids = {event.id for event in drainable_events.scalars().all()}

    assert summary.terminal_failed == 0
    assert persisted_event.id not in drainable_event_ids
