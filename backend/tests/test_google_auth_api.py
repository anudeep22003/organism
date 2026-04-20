"""API tests for the new Authlib-backed auth router surface."""

from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from core.auth.models.user import User
from core.auth_v2.models import GoogleOAuthAccount


def _google_token_payload(
    *,
    sub: str,
    email: str,
    refresh_token: str | None = "google-refresh-token",
) -> dict:
    payload: dict = {
        "access_token": "google-access-token",
        "id_token": "google-id-token",
        "scope": "openid email profile",
        "expires_at": 1_893_456_000,
        "userinfo": {
            "sub": sub,
            "email": email,
            "email_verified": True,
            "name": "Test User",
            "picture": "https://example.com/avatar.png",
        },
    }
    if refresh_token is not None:
        payload["refresh_token"] = refresh_token
    return payload


async def test_google_auth_login_redirects_to_google(api_client: AsyncClient) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_redirect = AsyncMock(
        return_value=RedirectResponse(
            url="https://accounts.google.com/o/oauth2/auth",
            status_code=307,
        )
    )

    with patch(
        "core.auth_v2.router.oauth.create_client", return_value=mock_google_client
    ):
        response = await api_client.get("/api/auth/login", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"].startswith("https://accounts.google.com/")


async def test_google_auth_callback_creates_user_and_google_account(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-create@example.com"
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        return_value=_google_token_payload(
            sub="google-sub-create",
            email=created_email,
        )
    )

    try:
        with patch(
            "core.auth_v2.router.oauth.create_client", return_value=mock_google_client
        ):
            response = await api_client.get(
                "/api/auth/callback", follow_redirects=False
            )

        assert response.status_code in {302, 307}
        assert response.headers["location"] == "http://localhost:5173/auth/success"

        user = await db_session.scalar(select(User).where(User.email == created_email))
        assert user is not None

        google_account = await db_session.scalar(
            select(GoogleOAuthAccount).where(
                GoogleOAuthAccount.google_sub == "google-sub-create"
            )
        )
        assert google_account is not None
        assert google_account.user_id == user.id
        assert google_account.refresh_token == "google-refresh-token"
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()


async def test_google_auth_callback_autolinks_existing_user_by_email(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        return_value=_google_token_payload(
            sub="google-sub-autolink",
            email=user.email,
        )
    )

    with patch(
        "core.auth_v2.router.oauth.create_client", return_value=mock_google_client
    ):
        response = await api_client.get("/api/auth/callback", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/success"

    google_account = await db_session.scalar(
        select(GoogleOAuthAccount).where(
            GoogleOAuthAccount.google_sub == "google-sub-autolink"
        )
    )
    assert google_account is not None
    assert google_account.user_id == user.id


async def test_google_auth_callback_failure_redirects_to_frontend_failure(
    api_client: AsyncClient,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        side_effect=RuntimeError("oauth exchange failed")
    )

    with patch(
        "core.auth_v2.router.oauth.create_client", return_value=mock_google_client
    ):
        response = await api_client.get("/api/auth/callback", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/failure"


async def test_google_auth_me_route_is_not_mounted(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/me")

    assert response.status_code == 404


async def test_existing_auth_router_stays_mounted(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/legacy-auth/me")

    assert response.status_code == 401
