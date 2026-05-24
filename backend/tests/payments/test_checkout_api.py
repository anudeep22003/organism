import uuid
from collections.abc import AsyncGenerator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.config import ACCESS_TOKEN_COOKIE_NAME
from core.auth.models import User
from core.auth.security import AccessTokenManager
from core.payments.models import CheckoutSession, Plan, StripeCustomer, Subscription


def make_auth_cookie_header(user_id: uuid.UUID) -> dict[str, str]:
    token = AccessTokenManager().create_access_token(user_id)
    return {"cookie": f"{ACCESS_TOKEN_COOKIE_NAME}={token}"}


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


async def seed_active_subscription(
    db_session: AsyncSession,
    user: User,
    stripe_customer: StripeCustomer,
) -> Subscription:
    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user.id,
        stripe_customer_record_id=stripe_customer.id,
        stripe_subscription_id=f"sub_test_{uuid.uuid4().hex[:14]}",
        stripe_customer_id=stripe_customer.stripe_customer_id,
        status="active",
        price_id="price_1TVTbWAMWKJyocPO4ayR6keZ",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
        cancel_at_period_end=False,
        canceled_at=None,
        trial_end=None,
        raw={"id": "placeholder", "status": "active"},
    )
    db_session.add(subscription)
    await db_session.commit()
    await db_session.refresh(subscription)
    return subscription


async def seed_plan(
    db_session: AsyncSession,
    *,
    plan_id: str | None = None,
    stripe_price_id: str | None = None,
    is_active: bool = True,
    sort_order: int = 0,
) -> Plan:
    plan = Plan(
        plan_id=plan_id or f"pro_monthly_{uuid.uuid4().hex[:8]}",
        display_name="Pro",
        description="For building stories.",
        stripe_price_id=stripe_price_id or f"price_test_{uuid.uuid4().hex[:14]}",
        entitlement_feature="pro_tier",
        features=[
            {"label": "Story generation"},
            {"label": "Character rendering", "description": "Render story characters."},
        ],
        amount_minor=1200,
        currency="usd",
        interval="month",
        is_active=is_active,
        sort_order=sort_order,
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


def make_stripe_client_mock(*, checkout_url: str) -> MagicMock:
    stripe_session = MagicMock()
    stripe_session.id = f"cs_test_{uuid.uuid4().hex[:14]}"
    stripe_session.status = "open"
    stripe_session.payment_status = "unpaid"
    stripe_session.amount_total = 1200
    stripe_session.currency = "usd"
    stripe_session.payment_intent = None
    stripe_session.subscription = None
    stripe_session.customer = f"cus_test_{uuid.uuid4().hex[:14]}"
    stripe_session.expires_at = int(
        (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()
    )
    stripe_session.url = checkout_url
    stripe_session.to_dict.return_value = {"id": stripe_session.id}

    stripe_client = MagicMock()
    stripe_client.v1.subscriptions.list_async = AsyncMock(
        return_value=MagicMock(data=[])
    )
    stripe_client.v1.checkout.sessions.create_async = AsyncMock(
        return_value=stripe_session
    )
    return stripe_client


@pytest.mark.asyncio
async def test_list_plans_is_public_and_hides_internal_billing_fields(
    api_client: AsyncClient,
    plan_factory: Callable[..., Awaitable[Plan]],
) -> None:
    active_plan = await plan_factory(
        plan_id=f"pro_monthly_{uuid.uuid4().hex[:8]}",
        stripe_price_id=f"price_active_{uuid.uuid4().hex[:14]}",
        sort_order=1,
    )
    await plan_factory(
        plan_id=f"inactive_{uuid.uuid4().hex[:8]}",
        stripe_price_id=f"price_inactive_{uuid.uuid4().hex[:14]}",
        is_active=False,
    )

    response = await api_client.get("/api/billing/plans")

    assert response.status_code == 200
    body = response.json()
    matching_plans = [
        plan for plan in body["plans"] if plan["planId"] == active_plan.plan_id
    ]
    assert len(matching_plans) == 1
    plan_body = matching_plans[0]
    assert plan_body["displayName"] == "Pro"
    assert plan_body["price"] == {
        "amountMinor": 1200,
        "currency": "usd",
        "interval": "month",
    }
    assert plan_body["features"][0] == {
        "label": "Story generation",
        "description": None,
    }
    assert "id" not in plan_body
    assert "stripePriceId" not in plan_body
    assert "entitlementFeature" not in plan_body
    assert all(not plan["planId"].startswith("inactive_") for plan in body["plans"])


@pytest.mark.asyncio
async def test_create_checkout_session_blocks_when_user_has_active_subscription(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    plan_factory: Callable[..., Awaitable[Plan]],
) -> None:
    stripe_customer = await seed_stripe_customer(
        db_session,
        user,
        stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:14]}",
    )
    plan = await plan_factory()
    await seed_active_subscription(db_session, user, stripe_customer)

    response = await api_client.post(
        "/api/billing/create-checkout-session",
        headers=make_auth_cookie_header(user.id),
        json={"planId": plan.plan_id},
    )

    checkout_sessions = await db_session.execute(
        select(CheckoutSession).where(CheckoutSession.user_id == user.id)
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "User already has an active subscription"}
    assert list(checkout_sessions.scalars().all()) == []


@pytest.mark.asyncio
async def test_create_checkout_session_uses_plan_id_to_resolve_stripe_price(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    plan_factory: Callable[..., Awaitable[Plan]],
) -> None:
    stripe_customer = await seed_stripe_customer(
        db_session,
        user,
        stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:14]}",
    )
    plan = await plan_factory(
        plan_id=f"pro_monthly_{uuid.uuid4().hex[:8]}",
        stripe_price_id=f"price_plan_{uuid.uuid4().hex[:14]}",
    )
    checkout_url = "https://checkout.stripe.test/session"
    stripe_client = make_stripe_client_mock(checkout_url=checkout_url)

    with patch(
        "core.payments.services.payments.get_stripe_client",
        return_value=stripe_client,
    ):
        response = await api_client.post(
            "/api/billing/create-checkout-session",
            headers=make_auth_cookie_header(user.id),
            json={"planId": plan.plan_id, "returnPath": "/story/123"},
        )

    assert response.status_code == 200
    assert response.json() == {"checkoutUrl": checkout_url}
    create_call = stripe_client.v1.checkout.sessions.create_async.await_args
    assert create_call is not None
    params = create_call.kwargs["params"]
    assert params["customer"] == stripe_customer.stripe_customer_id
    assert params["line_items"] == [{"price": plan.stripe_price_id, "quantity": 1}]
    assert params["mode"] == "subscription"
    assert params["success_url"].endswith("/payments/success?returnPath=%2Fstory%2F123")


@pytest.mark.asyncio
async def test_create_checkout_session_rejects_missing_plan_id(
    api_client: AsyncClient,
    user: User,
) -> None:
    response = await api_client.post(
        "/api/billing/create-checkout-session",
        headers=make_auth_cookie_header(user.id),
        json={"planId": f"missing_{uuid.uuid4().hex[:8]}"},
    )

    assert response.status_code == 404
