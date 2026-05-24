import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.config import ACCESS_TOKEN_COOKIE_NAME
from core.auth.models import User
from core.auth.security import AccessTokenManager
from core.payments.models import Entitlement, Plan, StripeCustomer, Subscription


def make_auth_cookie_header(user_id: uuid.UUID) -> dict[str, str]:
    token = AccessTokenManager().create_access_token(user_id)
    return {"cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}"}


async def clear_entitlements(db_session: AsyncSession, user: User) -> None:
    await db_session.execute(delete(Entitlement).where(Entitlement.user_id == user.id))
    await db_session.commit()


async def seed_stripe_customer(
    db_session: AsyncSession,
    user: User,
) -> StripeCustomer:
    stripe_customer_id = f"cus_test_{uuid.uuid4().hex[:14]}"
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


async def seed_entitlement(
    db_session: AsyncSession,
    user: User,
    *,
    feature: str = "pro_tier",
    source: str = "manual",
    valid_until: datetime | None = None,
) -> Entitlement:
    entitlement = Entitlement(
        user_id=user.id,
        feature=feature,
        source=source,
        source_id=None,
        valid_from=datetime.now(timezone.utc) - timedelta(minutes=1),
        valid_until=valid_until,
    )
    db_session.add(entitlement)
    await db_session.commit()
    await db_session.refresh(entitlement)
    return entitlement


async def seed_subscription(
    db_session: AsyncSession,
    user: User,
    stripe_customer: StripeCustomer,
    *,
    status: str,
    price_id: str | None = None,
    cancel_at_period_end: bool = False,
) -> Subscription:
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        stripe_customer_record_id=stripe_customer.id,
        stripe_subscription_id=f"sub_test_{uuid.uuid4().hex[:14]}",
        stripe_customer_id=stripe_customer.stripe_customer_id,
        status=status,
        price_id=price_id or f"price_test_{uuid.uuid4().hex[:14]}",
        current_period_start=now - timedelta(days=1),
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=cancel_at_period_end,
        canceled_at=now if status == "canceled" else None,
        trial_end=now + timedelta(days=7) if status == "trialing" else None,
        raw={"id": "placeholder", "status": status},
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


async def seed_plan(
    db_session: AsyncSession,
    *,
    stripe_price_id: str,
    plan_id: str | None = None,
) -> Plan:
    plan = Plan(
        plan_id=plan_id or f"pro_monthly_{uuid.uuid4().hex[:8]}",
        display_name="Pro",
        description="For building stories.",
        stripe_price_id=stripe_price_id,
        entitlement_feature="pro_tier",
        features=[{"label": "Story generation"}],
        amount_minor=1200,
        currency="usd",
        interval="month",
        is_active=True,
        sort_order=0,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest_asyncio.fixture
async def plan_factory(
    db_session: AsyncSession,
) -> AsyncGenerator[Callable[..., Awaitable[Plan]], None]:
    created_plan_ids: list[uuid.UUID] = []

    async def _create_plan(**kwargs: Any) -> Plan:
        plan = await seed_plan(db_session, **kwargs)
        created_plan_ids.append(plan.id)
        return plan

    yield _create_plan

    if created_plan_ids:
        await db_session.execute(delete(Plan).where(Plan.id.in_(created_plan_ids)))
        await db_session.commit()


@pytest.mark.asyncio
async def test_billing_me_subscribe_when_no_customer_subscription_or_entitlement(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    await clear_entitlements(db_session, user)

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "hasStripeCustomer": False,
        "hasActiveEntitlement": False,
        "activeEntitlements": [],
        "subscription": None,
        "canStartCheckout": True,
        "recommendedAction": "subscribe",
    }


@pytest.mark.asyncio
async def test_billing_me_manage_subscription_for_active_subscription_with_access(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    stripe_customer = await seed_stripe_customer(db_session, user)
    await seed_subscription(db_session, user, stripe_customer, status="active")

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hasStripeCustomer"] is True
    assert body["hasActiveEntitlement"] is True
    assert body["subscription"]["status"] == "active"
    assert body["canStartCheckout"] is False
    assert body["recommendedAction"] == "manage_subscription"


@pytest.mark.asyncio
async def test_billing_me_trial_active_for_trialing_subscription_with_access(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    stripe_customer = await seed_stripe_customer(db_session, user)
    await seed_subscription(db_session, user, stripe_customer, status="trialing")

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subscription"]["status"] == "trialing"
    assert body["subscription"]["trialEndsAt"] is not None
    assert body["canStartCheckout"] is False
    assert body["recommendedAction"] == "trial_active"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["past_due", "unpaid"])
async def test_billing_me_payment_failed_for_failed_payment_states(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    status: str,
) -> None:
    stripe_customer = await seed_stripe_customer(db_session, user)
    await seed_subscription(db_session, user, stripe_customer, status=status)

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subscription"]["status"] == status
    assert body["canStartCheckout"] is False
    assert body["recommendedAction"] == "payment_failed"


@pytest.mark.asyncio
async def test_billing_me_resubscribe_for_canceled_subscription_without_access(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    await clear_entitlements(db_session, user)
    stripe_customer = await seed_stripe_customer(db_session, user)
    await seed_subscription(db_session, user, stripe_customer, status="canceled")

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hasActiveEntitlement"] is False
    assert body["subscription"]["status"] == "canceled"
    assert body["canStartCheckout"] is True
    assert body["recommendedAction"] == "resubscribe"


@pytest.mark.asyncio
async def test_billing_me_none_for_manual_entitlement_without_subscription(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    await clear_entitlements(db_session, user)
    entitlement = await seed_entitlement(db_session, user, source="manual")

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hasActiveEntitlement"] is True
    assert body["activeEntitlements"] == [
        {"feature": entitlement.feature, "validUntil": None}
    ]
    assert body["subscription"] is None
    assert body["canStartCheckout"] is False
    assert body["recommendedAction"] == "none"


@pytest.mark.asyncio
async def test_billing_me_maps_subscription_price_to_public_plan(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    plan_factory: Callable[..., Awaitable[Plan]],
) -> None:
    stripe_customer = await seed_stripe_customer(db_session, user)
    plan = await plan_factory(
        stripe_price_id=f"price_test_{uuid.uuid4().hex[:14]}",
        plan_id=f"pro_monthly_{uuid.uuid4().hex[:8]}",
    )
    await seed_subscription(
        db_session,
        user,
        stripe_customer,
        status="active",
        price_id=plan.stripe_price_id,
    )

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    subscription = response.json()["subscription"]
    assert subscription["planId"] == plan.plan_id
    assert subscription["planName"] == plan.display_name
    assert "priceId" not in subscription


@pytest.mark.asyncio
async def test_billing_me_allows_missing_plan_mapping(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    stripe_customer = await seed_stripe_customer(db_session, user)
    await seed_subscription(
        db_session,
        user,
        stripe_customer,
        status="active",
        price_id=f"price_missing_{uuid.uuid4().hex[:14]}",
    )

    response = await api_client.get(
        "/api/billing/me",
        headers=make_auth_cookie_header(user.id),
    )

    assert response.status_code == 200
    subscription = response.json()["subscription"]
    assert subscription["planId"] is None
    assert subscription["planName"] is None
