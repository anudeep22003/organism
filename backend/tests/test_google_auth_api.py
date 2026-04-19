"""API tests for the placeholder Google auth v2 router."""

from httpx import AsyncClient


async def test_google_auth_login_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/google-auth/login")

    assert response.status_code == 200
    assert response.json() == {
        "endpoint": "login",
        "status": "NOT_IMPLEMENTED",
        "message": "google auth v2 login is not implemented yet",
    }


async def test_google_auth_callback_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/google-auth/callback")

    assert response.status_code == 200
    assert response.json() == {
        "endpoint": "callback",
        "status": "NOT_IMPLEMENTED",
        "message": "google auth v2 callback is not implemented yet",
    }


async def test_google_auth_me_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/google-auth/me")

    assert response.status_code == 200
    assert response.json() == {
        "endpoint": "me",
        "status": "NOT_IMPLEMENTED",
        "message": "google auth v2 me is not implemented yet",
    }


async def test_existing_auth_router_stays_mounted(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/me")

    assert response.status_code == 401
