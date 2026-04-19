"""API tests for the new Authlib-backed auth router surface."""

from httpx import AsyncClient


async def test_google_auth_login_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/login", follow_redirects=False)

    assert response.status_code in {302, 307}
    assert response.headers["location"].startswith("https://accounts.google.com/")


async def test_google_auth_callback_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/callback")

    assert response.status_code == 200
    assert response.json() == {}


async def test_google_auth_me_placeholder(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json() == {}


async def test_existing_auth_router_stays_mounted(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/legacy-auth/me")

    assert response.status_code == 401
