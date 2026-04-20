from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import RedirectResponse

from core.auth.models.user import User
from core.auth_v2.config import ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from core.auth_v2.models import AuthSession, GoogleOAuthAccount


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
        "core.auth_v2.router.oauth.create_client", return_value=mock_google_client
    ):
        return await api_client.get("/api/auth/callback", follow_redirects=False)


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


async def test_google_auth_callback_creates_user_google_account_and_session(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created_email = "callback-create@example.com"

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
        )
        assert old_token_response.status_code == 401
    finally:
        await db_session.execute(delete(User).where(User.email == created_email))
        await db_session.commit()


async def test_refresh_without_cookie_returns_401(api_client: AsyncClient) -> None:
    response = await api_client.post("/api/auth/refresh")
    assert response.status_code == 401


async def test_refresh_rejects_legacy_sha256_style_session_hash(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
) -> None:
    from datetime import timedelta

    from core.auth_v2.utils import get_current_datetime_utc

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
    )

    assert response.status_code == 401


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
        )

        assert logout_response.status_code == 204
        assert not logout_response.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        assert not logout_response.cookies.get(REFRESH_TOKEN_COOKIE_NAME)

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


async def test_existing_auth_router_stays_mounted(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/legacy-auth/me")

    assert response.status_code == 401
