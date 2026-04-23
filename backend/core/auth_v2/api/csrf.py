import hmac
import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..config import CSRF_TOKEN_COOKIE_NAME, CSRF_TOKEN_HEADER_NAME

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Enforce double-submit CSRF validation for unsafe cookie-auth requests."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.method not in _UNSAFE_METHODS:
            return await call_next(request)

        # Legacy auth routes still use the shared refresh_token cookie name but do not
        # issue an auth_v2 csrf_token cookie yet. Bypass validation in that case until
        # the old auth stack is removed and cookie auth is fully standardized.
        if CSRF_TOKEN_COOKIE_NAME not in request.cookies:
            return await call_next(request)

        csrf_cookie = request.cookies.get(CSRF_TOKEN_COOKIE_NAME)
        csrf_header = request.headers.get(CSRF_TOKEN_HEADER_NAME)

        if csrf_cookie is None or csrf_header is None:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token validation failed"},
            )

        if not hmac.compare_digest(csrf_cookie, csrf_header):
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token validation failed"},
            )

        return await call_next(request)
