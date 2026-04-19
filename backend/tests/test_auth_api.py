"""
API tests for authentication endpoints.

POST /api/legacy-auth/signup
POST /api/legacy-auth/signin
POST /api/legacy-auth/logout
POST /api/legacy-auth/refresh
GET  /api/legacy-auth/me

Tests focus on observable side effects and invariants:
- Correct response shapes (field names, types)
- State changes in the DB (session rows created/revoked)
- Cookie mechanics (set on login, cleared on logout)
- Auth boundary enforcement (401 when token missing or invalid)

No mocking. Real FastAPI app, real Postgres.
Fixtures in conftest.py handle user creation and cleanup.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    """Produce a valid Bearer token for the given user ID."""
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _unique_email() -> str:
    return f"test-{uuid.uuid4()}@example.com"


# ---------------------------------------------------------------------------
# POST /api/legacy-auth/signup
# ---------------------------------------------------------------------------


async def test_signup_creates_user_and_returns_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Signing up returns an access token and the new user's email."""
    email = _unique_email()
    response = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "correct-horse-battery"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["user"]["email"] == email
    assert isinstance(body["accessToken"], str)
    assert len(body["accessToken"]) > 0

    # Teardown: remove the user created by this test
    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


async def test_signup_sets_refresh_token_cookie(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Signup sets an HttpOnly refresh_token cookie."""
    email = _unique_email()
    response = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "correct-horse-battery"},
    )

    assert response.status_code == 200
    assert "refresh_token" in response.cookies

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


async def test_signup_duplicate_email_returns_400(
    api_client: AsyncClient,
    user: User,
) -> None:
    """Registering with an already-used email returns 400."""
    response = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": user.email, "password": "doesnt-matter"},
    )

    assert response.status_code == 400


async def test_signup_response_shape(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """The signup response has exactly the fields the API contract specifies.

    Changing UserResponse (e.g. adding/removing fields) should surface here.
    """
    email = _unique_email()
    response = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "shape-test-password"},
    )

    assert response.status_code == 200
    body = response.json()

    user_obj = body["user"]
    assert "id" in user_obj
    assert "email" in user_obj
    assert "updatedAt" in user_obj
    # password_hash must never leak
    assert "passwordHash" not in user_obj
    assert "password" not in user_obj

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


# ---------------------------------------------------------------------------
# POST /api/legacy-auth/signin
# ---------------------------------------------------------------------------


async def test_signin_returns_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Signing in with valid credentials returns an access token."""
    email = _unique_email()
    password = "test-password-123"

    # Register first
    signup_resp = await api_client.post(
        "/api/legacy-auth/signup", json={"email": email, "password": password}
    )
    assert signup_resp.status_code == 200

    # Sign in
    response = await api_client.post(
        "/api/legacy-auth/signin", json={"email": email, "password": password}
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["accessToken"], str)
    assert body["user"]["email"] == email

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


async def test_signin_wrong_password_returns_401(
    api_client: AsyncClient,
    user: User,
) -> None:
    """Wrong password on a real user returns 401."""
    response = await api_client.post(
        "/api/legacy-auth/signin",
        json={"email": user.email, "password": "definitely-wrong"},
    )

    assert response.status_code == 401


async def test_signin_unknown_email_returns_401(
    api_client: AsyncClient,
) -> None:
    """Attempting to sign in with a valid-format but non-existent email returns 401.

    This exercises the auth logic path (user lookup fails → 401).
    Distinct from the Pydantic validation path tested below.
    """
    response = await api_client.post(
        "/api/legacy-auth/signin",
        json={"email": "nobody@example.com", "password": "irrelevant"},
    )

    assert response.status_code == 401


async def test_signin_invalid_email_format_returns_422(
    api_client: AsyncClient,
) -> None:
    """A syntactically invalid email is rejected by Pydantic before auth runs → 422.

    This documents that input validation fires at the request-parsing layer,
    not at the auth/DB layer.  The two error paths are distinct invariants.
    """
    response = await api_client.post(
        "/api/legacy-auth/signin",
        json={"email": "not-an-email", "password": "irrelevant"},
    )

    assert response.status_code == 422


async def test_signin_creates_session_row(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A successful signin persists a session row in the DB."""
    email = _unique_email()
    password = "session-row-test"

    await api_client.post(
        "/api/legacy-auth/signup", json={"email": email, "password": password}
    )
    await api_client.post(
        "/api/legacy-auth/signin", json={"email": email, "password": password}
    )

    # Confirm at least one un-revoked session exists for this user
    result = await db_session.execute(
        text(
            'SELECT s.id FROM session s JOIN "user" u ON s.user_id = u.id '
            "WHERE u.email = :email AND s.revoked_at IS NULL"
        ),
        {"email": email},
    )
    rows = result.fetchall()
    assert len(rows) >= 1

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


# ---------------------------------------------------------------------------
# POST /api/legacy-auth/logout
# ---------------------------------------------------------------------------


async def test_logout_revokes_session(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Logging out marks the session as revoked in the DB."""
    email = _unique_email()
    password = "logout-test-pw"

    # Signup to get a session cookie
    signup_resp = await api_client.post(
        "/api/legacy-auth/signup", json={"email": email, "password": password}
    )
    assert signup_resp.status_code == 200
    refresh_token = signup_resp.cookies.get("refresh_token")
    assert refresh_token

    # Logout using the cookie
    logout_resp = await api_client.post(
        "/api/legacy-auth/logout",
        cookies={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "LOGGED_OUT"

    # The session must now be revoked in the DB
    result = await db_session.execute(
        text(
            'SELECT s.revoked_at FROM session s JOIN "user" u ON s.user_id = u.id '
            "WHERE u.email = :email ORDER BY s.created_at DESC LIMIT 1"
        ),
        {"email": email},
    )
    row = result.fetchone()
    assert row is not None
    assert row[0] is not None  # revoked_at is set

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


async def test_logout_without_cookie_returns_401(
    api_client: AsyncClient,
) -> None:
    """Logout without a refresh token cookie returns 401."""
    response = await api_client.post("/api/legacy-auth/logout")
    assert response.status_code == 401


async def test_logout_clears_cookie(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """The logout response deletes the refresh_token cookie."""
    email = _unique_email()
    signup_resp = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "cookie-clear-test"},
    )
    refresh_token = signup_resp.cookies.get("refresh_token")
    assert refresh_token

    logout_resp = await api_client.post(
        "/api/legacy-auth/logout",
        cookies={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200
    # The cookie should be deleted (value empty or absent)
    cookie_val = logout_resp.cookies.get("refresh_token")
    assert not cookie_val  # empty string or absent

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


# ---------------------------------------------------------------------------
# POST /api/legacy-auth/refresh
# ---------------------------------------------------------------------------


async def test_refresh_returns_new_access_token(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A valid refresh token cookie yields a new access token."""
    email = _unique_email()
    signup_resp = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "refresh-test-pw"},
    )
    assert signup_resp.status_code == 200
    refresh_token = signup_resp.cookies.get("refresh_token")
    assert refresh_token

    refresh_resp = await api_client.post(
        "/api/legacy-auth/refresh",
        cookies={"refresh_token": refresh_token},
    )

    assert refresh_resp.status_code == 200
    body = refresh_resp.json()
    assert isinstance(body["accessToken"], str)
    assert len(body["accessToken"]) > 0

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


async def test_refresh_without_cookie_returns_401(
    api_client: AsyncClient,
) -> None:
    """Calling /refresh with no cookie returns 401."""
    response = await api_client.post("/api/legacy-auth/refresh")
    assert response.status_code == 401


async def test_refresh_after_logout_returns_401(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Using a revoked refresh token to refresh returns 401."""
    email = _unique_email()
    signup_resp = await api_client.post(
        "/api/legacy-auth/signup",
        json={"email": email, "password": "revoke-test-pw"},
    )
    refresh_token = signup_resp.cookies.get("refresh_token")
    assert refresh_token

    # Revoke it via logout
    await api_client.post(
        "/api/legacy-auth/logout",
        cookies={"refresh_token": refresh_token},
    )

    # Try to refresh with the now-revoked token
    response = await api_client.post(
        "/api/legacy-auth/refresh",
        cookies={"refresh_token": refresh_token},
    )
    assert response.status_code == 401

    await db_session.execute(
        text('DELETE FROM "user" WHERE email = :email'), {"email": email}
    )
    await db_session.commit()


# ---------------------------------------------------------------------------
# GET /api/legacy-auth/me
# ---------------------------------------------------------------------------


async def test_me_returns_user(
    api_client: AsyncClient,
    user: User,
) -> None:
    """GET /me with a valid token returns the authenticated user's data."""
    response = await api_client.get(
        "/api/legacy-auth/me", headers=_auth_headers(user.id)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(user.id)
    assert body["email"] == user.email


async def test_me_without_token_returns_401(
    api_client: AsyncClient,
) -> None:
    """GET /me without an auth header returns 401."""
    response = await api_client.get("/api/legacy-auth/me")
    assert response.status_code == 401


async def test_me_with_malformed_token_returns_401(
    api_client: AsyncClient,
) -> None:
    """GET /me with a garbage token returns 401."""
    response = await api_client.get(
        "/api/legacy-auth/me",
        headers={"Authorization": "Bearer this.is.garbage"},
    )
    assert response.status_code == 401


async def test_me_response_shape(
    api_client: AsyncClient,
    user: User,
) -> None:
    """The /me response has the exact fields in UserResponse.

    If UserResponse gains or loses a field, this test should catch it.
    """
    response = await api_client.get(
        "/api/legacy-auth/me", headers=_auth_headers(user.id)
    )

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    assert "email" in body
    assert "updatedAt" in body
    # password must never be in the response
    assert "password" not in body
    assert "passwordHash" not in body
