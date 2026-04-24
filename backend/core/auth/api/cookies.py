from fastapi import Response

from ..config import (
    ACCESS_TOKEN_COOKIE_HTTPONLY,
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_COOKIE_PATH,
    ACCESS_TOKEN_COOKIE_SAMESITE,
    ACCESS_TOKEN_COOKIE_SECURE,
    CSRF_TOKEN_COOKIE_HTTPONLY,
    CSRF_TOKEN_COOKIE_NAME,
    CSRF_TOKEN_COOKIE_PATH,
    CSRF_TOKEN_COOKIE_SAMESITE,
    CSRF_TOKEN_COOKIE_SECURE,
    REFRESH_TOKEN_COOKIE_HTTPONLY,
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_PATH,
    REFRESH_TOKEN_COOKIE_SAMESITE,
    REFRESH_TOKEN_COOKIE_SECURE,
    REFRESH_TOKEN_TTL_SECONDS,
)


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        httponly=ACCESS_TOKEN_COOKIE_HTTPONLY,
        secure=ACCESS_TOKEN_COOKIE_SECURE,
        samesite=ACCESS_TOKEN_COOKIE_SAMESITE,
        max_age=None,
        path=ACCESS_TOKEN_COOKIE_PATH,
    )
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=REFRESH_TOKEN_COOKIE_HTTPONLY,
        secure=REFRESH_TOKEN_COOKIE_SECURE,
        samesite=REFRESH_TOKEN_COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        path=REFRESH_TOKEN_COOKIE_PATH,
    )
    response.set_cookie(
        key=CSRF_TOKEN_COOKIE_NAME,
        value=csrf_token,
        httponly=CSRF_TOKEN_COOKIE_HTTPONLY,
        secure=CSRF_TOKEN_COOKIE_SECURE,
        samesite=CSRF_TOKEN_COOKIE_SAMESITE,
        max_age=REFRESH_TOKEN_TTL_SECONDS,
        path=CSRF_TOKEN_COOKIE_PATH,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path=ACCESS_TOKEN_COOKIE_PATH,
        httponly=ACCESS_TOKEN_COOKIE_HTTPONLY,
        secure=ACCESS_TOKEN_COOKIE_SECURE,
        samesite=ACCESS_TOKEN_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path=REFRESH_TOKEN_COOKIE_PATH,
        httponly=REFRESH_TOKEN_COOKIE_HTTPONLY,
        secure=REFRESH_TOKEN_COOKIE_SECURE,
        samesite=REFRESH_TOKEN_COOKIE_SAMESITE,
    )
    response.delete_cookie(
        key=CSRF_TOKEN_COOKIE_NAME,
        path=CSRF_TOKEN_COOKIE_PATH,
        httponly=CSRF_TOKEN_COOKIE_HTTPONLY,
        secure=CSRF_TOKEN_COOKIE_SECURE,
        samesite=CSRF_TOKEN_COOKIE_SAMESITE,
    )
