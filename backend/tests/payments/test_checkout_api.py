import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.config import ACCESS_TOKEN_COOKIE_NAME
from core.auth.models import User
from core.auth.security import AccessTokenManager
from core.payments.models import CheckoutSession, StripeCustomer, Subscription


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


@pytest.mark.asyncio
async def test_create_checkout_session_blocks_when_user_has_active_subscription(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    stripe_customer = await seed_stripe_customer(
        db_session,
        user,
        stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:14]}",
    )
    await seed_active_subscription(db_session, user, stripe_customer)

    response = await api_client.post(
        "/api/billing/create-checkout-session",
        headers=make_auth_cookie_header(user.id),
    )

    checkout_sessions = await db_session.execute(
        select(CheckoutSession).where(CheckoutSession.user_id == user.id)
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "User already has an active subscription"}
    assert list(checkout_sessions.scalars().all()) == []
