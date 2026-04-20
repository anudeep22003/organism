import uuid
from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger

from core.config import settings

from .api import get_auth_service, get_current_user_id_v2, get_request_client_context
from .config import (
    ACCESS_TOKEN_COOKIE_HTTPONLY,
    ACCESS_TOKEN_COOKIE_NAME,
    ACCESS_TOKEN_COOKIE_PATH,
    ACCESS_TOKEN_COOKIE_SAMESITE,
    ACCESS_TOKEN_COOKIE_SECURE,
    REFRESH_TOKEN_COOKIE_HTTPONLY,
    REFRESH_TOKEN_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_PATH,
    REFRESH_TOKEN_COOKIE_SAMESITE,
    REFRESH_TOKEN_COOKIE_SECURE,
    REFRESH_TOKEN_TTL_SECONDS,
)
from .exceptions import InvalidRefreshTokenError, UserNotFoundError
from .schemas import UserResponse
from .service import AuthService

router = APIRouter(prefix="/auth", tags=["auth", "google-auth"])


oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_oauth_client_id,
    client_secret=settings.google_oauth_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
    },
)


def _frontend_auth_redirect(path: str) -> str:
    frontend_base_url = settings.frontend_url or settings.cors_origins
    return f"{frontend_base_url.rstrip('/')}{path}"


def _set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
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


def _clear_auth_cookies(response: Response) -> None:
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


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    google = oauth.create_client("google")
    redirect_uri = str(request.url_for("callback"))
    # The callback URL is the endpoint that Google will redirect the user to after they complete authentication.
    # Here, request.url_for("callback") dynamically generates the absolute URL for the "/callback" route,
    # ensuring that OAuth will return the authenticated user to the correct handler in this FastAPI app.
    logger.info(f"Redirecting to Google OAuth: {redirect_uri}")
    return await google.authorize_redirect(  # type: ignore[no-any-return]
        request,
        redirect_uri,
        access_type="offline",  # request refresh token (for future Google API use)
        prompt="consent",  # ensure refresh token is returned
    )


@router.get("/callback")
async def callback(
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_context: Annotated[
        tuple[str | None, str | None], Depends(get_request_client_context)
    ],
) -> RedirectResponse:
    try:
        google = oauth.create_client("google")
        token = await google.authorize_access_token(request)
        user_agent, ip = client_context
        result = await service.handle_google_callback(
            token=token,
            user_agent=user_agent,
            ip=ip,
        )
        response = RedirectResponse(url=_frontend_auth_redirect("/auth/success"))
        _set_auth_cookies(
            response,
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
        )
        return response
    except Exception as e:
        logger.error(f"Error authorizing access token: {e}")
        return RedirectResponse(url=_frontend_auth_redirect("/auth/failure"))


@router.get("/me")
async def me(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id_v2)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserResponse:
    try:
        user = await service.get_current_user(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.post("/refresh", status_code=status.HTTP_204_NO_CONTENT)
async def refresh(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_NAME)
    ] = None,
) -> Response:
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    try:
        tokens = await service.refresh_session(refresh_token)
    except InvalidRefreshTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    _set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_NAME)
    ] = None,
) -> Response:
    await service.logout(refresh_token)
    _clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
