import pytest
from fastapi import Response

from core.auth.api import cookies
from core.auth.config import CSRF_TOKEN_COOKIE_NAME


def _set_cookie_headers(response: Response) -> list[str]:
    return [
        value.decode("latin-1")
        for key, value in response.raw_headers
        if key.lower() == b"set-cookie"
    ]


def test_set_auth_cookies_uses_configured_csrf_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cookies.settings, "csrf_cookie_domain", "dekatha.com")
    response = Response()

    cookies.set_auth_cookies(
        response,
        access_token="access",
        refresh_token="refresh",
        csrf_token="csrf",
    )

    csrf_headers = [
        header
        for header in _set_cookie_headers(response)
        if header.startswith(f"{CSRF_TOKEN_COOKIE_NAME}=")
    ]
    assert any("Domain=dekatha.com" in header for header in csrf_headers)
    assert any(
        "Max-Age=0" in header and "Domain=" not in header for header in csrf_headers
    )


def test_set_auth_cookies_leaves_csrf_host_only_without_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cookies.settings, "csrf_cookie_domain", None)
    response = Response()

    cookies.set_auth_cookies(
        response,
        access_token="access",
        refresh_token="refresh",
        csrf_token="csrf",
    )

    csrf_headers = [
        header
        for header in _set_cookie_headers(response)
        if header.startswith(f"{CSRF_TOKEN_COOKIE_NAME}=")
    ]
    assert len(csrf_headers) == 1
    assert "Domain=" not in csrf_headers[0]


def test_clear_auth_cookies_deletes_domain_and_host_only_csrf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cookies.settings, "csrf_cookie_domain", "dekatha.com")
    response = Response()

    cookies.clear_auth_cookies(response)

    csrf_headers = [
        header
        for header in _set_cookie_headers(response)
        if header.startswith(f"{CSRF_TOKEN_COOKIE_NAME}=")
    ]
    assert any(
        "Max-Age=0" in header and "Domain=dekatha.com" in header
        for header in csrf_headers
    )
    assert any(
        "Max-Age=0" in header and "Domain=" not in header for header in csrf_headers
    )
