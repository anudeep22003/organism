from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.auth_v2.repository import AuthRepositoryV2


async def test_create_google_oauth_account_links_to_user(
    db_session: AsyncSession,
    user: User,
) -> None:
    repo = AuthRepositoryV2(db_session)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    google_account = await repo.google_oauth_account.create_google_oauth_account(
        user_id=user.id,
        google_sub="google-sub-1",
        email=user.email,
        email_verified=True,
        access_token="access-token",
        refresh_token="refresh-token",
        id_token="id-token",
        scope="openid email profile",
        name="Test User",
        picture_url="https://example.com/avatar.png",
        token_expires_at=expires_at,
    )
    await db_session.commit()
    await db_session.refresh(google_account)

    assert google_account.user_id == user.id
    assert google_account.google_sub == "google-sub-1"
    assert google_account.refresh_token == "refresh-token"


async def test_get_google_oauth_account_by_sub_loads_linked_user(
    db_session: AsyncSession,
    user: User,
) -> None:
    repo = AuthRepositoryV2(db_session)

    await repo.google_oauth_account.create_google_oauth_account(
        user_id=user.id,
        google_sub="google-sub-2",
        email=user.email,
        email_verified=True,
        access_token="access-token",
    )
    await db_session.commit()

    google_account = await repo.google_oauth_account.get_google_oauth_account_by_sub(
        "google-sub-2"
    )

    assert google_account is not None
    assert google_account.user.id == user.id
    assert google_account.user.email == user.email


async def test_list_google_oauth_accounts_for_user_returns_all_accounts(
    db_session: AsyncSession,
    user: User,
) -> None:
    repo = AuthRepositoryV2(db_session)

    await repo.google_oauth_account.create_google_oauth_account(
        user_id=user.id,
        google_sub="google-sub-3",
        email=user.email,
        email_verified=True,
        access_token="first-token",
    )
    await repo.google_oauth_account.create_google_oauth_account(
        user_id=user.id,
        google_sub="google-sub-4",
        email=user.email,
        email_verified=False,
        access_token="second-token",
    )
    await db_session.commit()

    google_accounts = (
        await repo.google_oauth_account.list_google_oauth_accounts_for_user(user.id)
    )

    assert [account.google_sub for account in google_accounts] == [
        "google-sub-3",
        "google-sub-4",
    ]


async def test_update_google_oauth_account_updates_existing_row_in_place(
    db_session: AsyncSession,
    user: User,
) -> None:
    repo = AuthRepositoryV2(db_session)
    google_account = await repo.google_oauth_account.create_google_oauth_account(
        user_id=user.id,
        google_sub="google-sub-5",
        email=user.email,
        email_verified=False,
        access_token="old-access-token",
        refresh_token=None,
    )
    await db_session.commit()
    await db_session.refresh(google_account)

    updated_account = await repo.google_oauth_account.update_google_oauth_account(
        google_account,
        email="new-email@example.com",
        email_verified=True,
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        id_token="new-id-token",
        scope="openid email profile",
        name="Updated User",
        picture_url="https://example.com/new-avatar.png",
        token_expires_at=datetime.now(timezone.utc) + timedelta(hours=2),
    )
    await db_session.commit()
    await db_session.refresh(updated_account)

    assert updated_account.id == google_account.id
    assert updated_account.email == "new-email@example.com"
    assert updated_account.email_verified is True
    assert updated_account.access_token == "new-access-token"
    assert updated_account.refresh_token == "new-refresh-token"
