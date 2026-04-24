from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from core.auth.config import (
    ACCESS_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_HEADER_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
)
from core.auth.models import AuthSession, GoogleOAuthAccount, User
from core.auth.security import (
    CALLBACK_RATE_LIMIT_POLICY,
    LOGIN_RATE_LIMIT_POLICY,
    REFRESH_RATE_LIMIT_POLICY,
    get_encryptor,
    reset_auth_rate_limiter,
)
from core.config import settings


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    reset_auth_rate_limiter()


def _csrf_headers(api_client: AsyncClient) -> dict[str, str]:
    csrf_token = api_client.cookies.get(CSRF_TOKEN_COOKIE_NAME)
    assert csrf_token is not None
    return {CSRF_TOKEN_HEADER_NAME: csrf_token}


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


async def _login_via_callback(
    api_client: AsyncClient,
    *,
    email: str,
    sub: str,
    refresh_token: str | None = "google-refresh-token",
    headers: dict[str, str] | None = None,
) -> Response:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        return_value=_google_token_payload(
            sub=sub,
            email=email,
            refresh_token=refresh_token,
        )
    )
    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        return await api_client.get(
            "/api/auth/callback",
            headers=headers,
            follow_redirects=False,
        )


async def test_google_auth_login_redirects_to_google(api_client: AsyncClient) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_redirect = AsyncMock(
        return_value=RedirectResponse(
            url="https://accounts.google.com/o/oauth2/auth",
            status_code=307,
        )
    )

    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        response = await api_client.get("/api/auth/login", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"].startswith("https://accounts.google.com/")
    mock_google_client.authorize_redirect.assert_awaited_once()
    redirect_uri = mock_google_client.authorize_redirect.await_args.args[1]
    assert redirect_uri == f"{settings.api_url}/api/auth/callback"


async def test_google_auth_login_rate_limit_returns_429(
    api_client: AsyncClient,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_redirect = AsyncMock(
        return_value=RedirectResponse(
            url="https://accounts.google.com/o/oauth2/auth",
            status_code=307,
        )
    )
    headers = {"x-forwarded-for": "198.51.100.10"}

    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        for _ in range(LOGIN_RATE_LIMIT_POLICY.max_requests):
            response = await api_client.get(
                "/api/auth/login",
                headers=headers,
                follow_redirects=False,
            )
            assert response.status_code in {302, 307}

        response = await api_client.get(
            "/api/auth/login",
            headers=headers,
            follow_redirects=False,
        )

    assert response.status_code == 429


async def test_google_auth_callback_creates_user_google_account_and_session(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-create@example.com"
    encryptor = get_encryptor()

    try:
        response = await _login_via_callback(
            api_client,
            email=created_email,
            sub="google-sub-create",
        )

        assert response.status_code in {302, 307}
        assert response.headers["location"] == "http://localhost:5173/auth/success"
        assert response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        assert response.cookies.get(CSRF_TOKEN_COOKIE_NAME)

        user = await db_session.scalar(select(User).where(User.email == created_email))
        assert user is not None

        google_account = await db_session.scalar(
            select(GoogleOAuthAccount).where(
                GoogleOAuthAccount.google_sub == "google-sub-create"
            )
        )
        assert google_account is not None
        assert google_account.user_id == user.id
        assert google_account.refresh_token is not None
        assert google_account.id_token is not None
        assert encryptor.decrypt(google_account.access_token) == "google-access-token"
        assert encryptor.decrypt(google_account.refresh_token) == "google-refresh-token"
        assert encryptor.decrypt(google_account.id_token) == "google-id-token"
        assert user.password_hash.startswith("$argon2")

        sessions = await db_session.execute(
            select(AuthSession).where(AuthSession.user_id == user.id)
        )
        assert len(list(sessions.scalars().all())) == 1
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()


async def test_google_auth_callback_autolinks_existing_user_by_email(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    response = await _login_via_callback(
        api_client,
        email=user.email,
        sub="google-sub-autolink",
    )

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/success"

    google_account = await db_session.scalar(
        select(GoogleOAuthAccount).where(
            GoogleOAuthAccount.google_sub == "google-sub-autolink"
        )
    )
    assert google_account is not None
    assert google_account.user_id == user.id


async def test_google_auth_callback_encrypts_legacy_plaintext_refresh_token_on_relogin(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    encryptor = get_encryptor()
    google_account = GoogleOAuthAccount.create(
        user_id=user.id,
        google_sub="google-sub-legacy-refresh",
        email=user.email,
        email_verified=True,
        access_token="legacy-access-token",
        refresh_token="legacy-refresh-token",
        id_token="legacy-id-token",
        scope="openid email profile",
        name="Legacy User",
        picture_url="https://example.com/legacy-avatar.png",
    )
    db_session.add(google_account)
    await db_session.commit()

    response = await _login_via_callback(
        api_client,
        email=user.email,
        sub="google-sub-legacy-refresh",
        refresh_token=None,
    )

    assert response.status_code in {302, 307}

    await db_session.refresh(google_account)
    assert google_account.refresh_token is not None
    assert encryptor.decrypt(google_account.refresh_token) == "legacy-refresh-token"


async def test_google_auth_callback_failure_redirects_to_frontend_failure(
    api_client: AsyncClient,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        side_effect=RuntimeError("oauth exchange failed")
    )

    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        response = await api_client.get("/api/auth/callback", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/failure"


async def test_google_auth_callback_rate_limit_returns_429(
    api_client: AsyncClient,
) -> None:
    headers = {"x-forwarded-for": "198.51.100.20"}

    for _ in range(CALLBACK_RATE_LIMIT_POLICY.max_requests):
        response = await _login_via_callback(
            api_client,
            email="callback-limit@example.com",
            sub="google-sub-limit",
            headers=headers,
        )
        assert response.status_code in {302, 307}

    response = await _login_via_callback(
        api_client,
        email="callback-limit@example.com",
        sub="google-sub-limit",
        headers=headers,
    )

    assert response.status_code == 429


async def test_google_auth_callback_missing_userinfo_redirects_to_frontend_failure(
    api_client: AsyncClient,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        return_value={
            "access_token": "google-access-token",
            "id_token": "google-id-token",
            "scope": "openid email profile",
            "expires_at": 1_893_456_000,
        }
    )

    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        response = await api_client.get("/api/auth/callback", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/failure"


async def test_google_auth_callback_missing_required_profile_field_redirects_to_failure(
    api_client: AsyncClient,
) -> None:
    mock_google_client = MagicMock()
    mock_google_client.authorize_access_token = AsyncMock(
        return_value={
            "access_token": "google-access-token",
            "id_token": "google-id-token",
            "scope": "openid email profile",
            "expires_at": 1_893_456_000,
            "userinfo": {
                "sub": "google-sub-missing-email",
                "email_verified": True,
                "name": "Test User",
            },
        }
    )

    with patch(
        "core.auth.api.router.oauth.create_client",
        return_value=mock_google_client,
    ):
        response = await api_client.get("/api/auth/callback", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"] == "http://localhost:5173/auth/failure"


async def test_me_returns_current_user_from_access_cookie(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-me@example.com"

    try:
        response = await _login_via_callback(
            api_client,
            email=created_email,
            sub="google-sub-me",
        )
        assert response.status_code in {302, 307}

        me_response = await api_client.get("/api/auth/me")

        assert me_response.status_code == 200
        body = me_response.json()
        assert body["email"] == created_email
        assert "id" in body
        assert "updatedAt" in body
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()


async def test_me_without_access_cookie_returns_401(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/me")
    assert response.status_code == 401


async def test_refresh_rotates_session_and_sets_new_cookies(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-refresh@example.com"

    try:
        callback_response = await _login_via_callback(
            api_client,
            email=created_email,
            sub="google-sub-refresh",
        )
        assert callback_response.status_code in {302, 307}
        old_refresh_token = callback_response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        old_access_token = callback_response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert old_refresh_token is not None
        assert old_access_token is not None

        refresh_response = await api_client.post(
            "/api/auth/refresh",
            cookies={REFRESH_TOKEN_COOKIE_NAME: old_refresh_token},
            headers=_csrf_headers(api_client),
        )

        assert refresh_response.status_code == 204
        new_refresh_token = refresh_response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        new_access_token = refresh_response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert new_refresh_token is not None
        assert new_access_token is not None
        assert new_refresh_token != old_refresh_token
        assert new_access_token != old_access_token

        user = await db_session.scalar(select(User).where(User.email == created_email))
        assert user is not None
        session_rows = await db_session.execute(
            select(AuthSession).where(AuthSession.user_id == user.id)
        )
        sessions = list(session_rows.scalars().all())
        assert len(sessions) == 2
        revoked_sessions = [
            session for session in sessions if session.revoked_at is not None
        ]
        active_sessions = [
            session for session in sessions if session.revoked_at is None
        ]
        assert len(revoked_sessions) == 1
        assert len(active_sessions) == 1

        old_token_response = await api_client.post(
            "/api/auth/refresh",
            cookies={REFRESH_TOKEN_COOKIE_NAME: old_refresh_token},
            headers=_csrf_headers(api_client),
        )
        assert old_token_response.status_code == 401
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()


async def test_refresh_without_cookie_returns_401(api_client: AsyncClient) -> None:
    response = await api_client.post(
        "/api/auth/refresh",
        headers={CSRF_TOKEN_HEADER_NAME: "unused"},
    )
    assert response.status_code == 401


async def test_refresh_rejects_legacy_sha256_style_session_hash(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    from datetime import timedelta

    from core.auth.utils import get_current_datetime_utc

    session = AuthSession.create(
        user_id=user.id,
        refresh_token_hash="plain-sha256-style-hash",
        user_agent=None,
        ip=None,
        expires_at=get_current_datetime_utc() + timedelta(days=1),
    )
    db_session.add(session)
    await db_session.commit()
    refresh_token = f"{session.id}.legacysecret"

    response = await api_client.post(
        "/api/auth/refresh",
        cookies={REFRESH_TOKEN_COOKIE_NAME: refresh_token},
        headers={CSRF_TOKEN_HEADER_NAME: "legacysecret"},
    )

    assert response.status_code == 401


async def test_refresh_requires_csrf_header(api_client: AsyncClient) -> None:
    api_client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, "session.secret")
    api_client.cookies.set(CSRF_TOKEN_COOKIE_NAME, "csrf-token")

    response = await api_client.post("/api/auth/refresh")

    assert response.status_code == 403


async def test_refresh_rejects_mismatched_csrf_header(
    api_client: AsyncClient,
) -> None:
    api_client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, "session.secret")
    api_client.cookies.set(CSRF_TOKEN_COOKIE_NAME, "csrf-token")

    response = await api_client.post(
        "/api/auth/refresh",
        headers={CSRF_TOKEN_HEADER_NAME: "wrong-token"},
    )

    assert response.status_code == 403


async def test_refresh_rate_limit_returns_429(api_client: AsyncClient) -> None:
    headers = {
        "x-forwarded-for": "198.51.100.30",
        CSRF_TOKEN_HEADER_NAME: "csrf-token",
    }
    api_client.cookies.set(REFRESH_TOKEN_COOKIE_NAME, "session.secret")
    api_client.cookies.set(CSRF_TOKEN_COOKIE_NAME, "csrf-token")

    for _ in range(REFRESH_RATE_LIMIT_POLICY.max_requests):
        response = await api_client.post("/api/auth/refresh", headers=headers)
        assert response.status_code == 401

    response = await api_client.post("/api/auth/refresh", headers=headers)

    assert response.status_code == 429


async def test_logout_revokes_session_and_clears_cookies(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-logout@example.com"

    try:
        callback_response = await _login_via_callback(
            api_client,
            email=created_email,
            sub="google-sub-logout",
        )
        refresh_token = callback_response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        assert refresh_token is not None

        logout_response = await api_client.post(
            "/api/auth/logout",
            cookies={REFRESH_TOKEN_COOKIE_NAME: refresh_token},
            headers=_csrf_headers(api_client),
        )

        assert logout_response.status_code == 204
        assert not logout_response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert not logout_response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)
        assert not logout_response.cookies.get(CSRF_TOKEN_COOKIE_NAME)

        user = await db_session.scalar(select(User).where(User.email == created_email))
        assert user is not None
        session_rows = await db_session.execute(
            select(AuthSession).where(AuthSession.user_id == user.id)
        )
        sessions = list(session_rows.scalars().all())
        assert len(sessions) == 1
        assert sessions[0].revoked_at is not None

        me_response = await api_client.get("/api/auth/me")
        assert me_response.status_code == 401

        second_logout = await api_client.post(
            "/api/auth/logout",
            cookies={REFRESH_TOKEN_COOKIE_NAME: refresh_token},
        )
        assert second_logout.status_code == 204
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()
