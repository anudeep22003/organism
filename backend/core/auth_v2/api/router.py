import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger

from core.config import settings

from ..config import CSRF_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME
from ..exceptions import (
    AuthV2Error,
    InvalidRefreshTokenError,
    OAuthError,
    OAuthTokenExchangeError,
    UserNotFoundError,
)
from ..observability import log_auth_event
from ..schemas import UserResponse
from ..services import AuthService
from .cookies import clear_auth_cookies, set_auth_cookies
from .csrf import generate_csrf_token
from .dependencies import (
    enforce_callback_rate_limit,
    enforce_login_rate_limit,
    enforce_refresh_rate_limit,
    get_auth_service,
    get_current_user_id,
    get_request_client_context,
)
from .oauth_client import oauth

router = APIRouter(prefix="/auth", tags=["auth", "google-auth"])


def _frontend_auth_redirect(path: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}{path}"


def _google_callback_url() -> str:
    return f"{settings.api_url.rstrip('/')}/api/auth/callback"


@router.get("/login")
async def login(
    request: Request,
    _: Annotated[None, Depends(enforce_login_rate_limit)],
    client_context: Annotated[
        tuple[str | None, str | None], Depends(get_request_client_context)
    ],
) -> RedirectResponse:
    google = oauth.create_client("google")
    user_agent, ip = client_context
    log_auth_event(
        "auth.login.started",
        route=request.url.path,
        ip=ip,
        user_agent=user_agent,
    )
    return await google.authorize_redirect(  # type: ignore[no-any-return]
        request,
        _google_callback_url(),
        access_type="offline",
        prompt="consent",
    )


@router.get("/callback")
async def callback(
    request: Request,
    _: Annotated[None, Depends(enforce_callback_rate_limit)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_context: Annotated[
        tuple[str | None, str | None], Depends(get_request_client_context)
    ],
) -> RedirectResponse:
    user_agent, ip = client_context
    google_sub: str | None = None
    try:
        google = oauth.create_client("google")
        try:
            token = await google.authorize_access_token(request)
        except Exception as exc:
            raise OAuthTokenExchangeError(
                "Failed to exchange Google OAuth token"
            ) from exc
        userinfo = token.get("userinfo")
        if isinstance(userinfo, dict):
            sub = userinfo.get("sub")
            if isinstance(sub, str) and sub != "":
                google_sub = sub
        result = await service.handle_google_callback(
            token=token,
            user_agent=user_agent,
            ip=ip,
        )
        log_auth_event(
            "auth.login.succeeded",
            route=request.url.path,
            user_id=result.user_id,
            google_sub=google_sub,
            ip=ip,
            user_agent=user_agent,
        )
        response = RedirectResponse(url=_frontend_auth_redirect("/auth/success"))
        set_auth_cookies(
            response,
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
            csrf_token=generate_csrf_token(),
        )
        return response
    except OAuthError as exc:
        log_auth_event(
            "auth.oauth.callback.failed",
            level="warning",
            route=request.url.path,
            google_sub=google_sub,
            ip=ip,
            user_agent=user_agent,
            reason=type(exc).__name__,
        )
        return RedirectResponse(url=_frontend_auth_redirect("/auth/failure"))
    except AuthV2Error as exc:
        log_auth_event(
            "auth.login.failed",
            level="warning",
            route=request.url.path,
            google_sub=google_sub,
            ip=ip,
            user_agent=user_agent,
            reason=type(exc).__name__,
        )
        return RedirectResponse(url=_frontend_auth_redirect("/auth/failure"))
    except Exception:
        logger.exception("Unexpected auth callback failure")
        return RedirectResponse(url=_frontend_auth_redirect("/auth/failure"))


@router.get("/me")
async def me(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
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
    _: Annotated[None, Depends(enforce_refresh_rate_limit)],
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_context: Annotated[
        tuple[str | None, str | None], Depends(get_request_client_context)
    ],
    refresh_token: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_NAME)
    ] = None,
    csrf_token: Annotated[str | None, Cookie(alias=CSRF_TOKEN_COOKIE_NAME)] = None,
) -> Response:
    """Rotate the session tokens while preserving the current CSRF token."""

    user_agent, ip = client_context
    if refresh_token is None:
        log_auth_event(
            "auth.refresh.failed",
            level="warning",
            route="/api/auth/refresh",
            ip=ip,
            user_agent=user_agent,
            reason="MissingRefreshToken",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    try:
        tokens = await service.refresh_session(refresh_token)
    except InvalidRefreshTokenError as exc:
        log_auth_event(
            "auth.refresh.failed",
            level="warning",
            route="/api/auth/refresh",
            ip=ip,
            user_agent=user_agent,
            reason=type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        )
    log_auth_event(
        "auth.refresh.succeeded",
        route="/api/auth/refresh",
        user_id=tokens.user_id,
        ip=ip,
        user_agent=user_agent,
    )
    set_auth_cookies(
        response,
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        csrf_token=csrf_token or generate_csrf_token(),
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    client_context: Annotated[
        tuple[str | None, str | None], Depends(get_request_client_context)
    ],
    refresh_token: Annotated[
        str | None, Cookie(alias=REFRESH_TOKEN_COOKIE_NAME)
    ] = None,
) -> Response:
    user_agent, ip = client_context
    user_id = await service.logout(refresh_token)
    log_auth_event(
        "auth.logout.succeeded",
        route="/api/auth/logout",
        user_id=user_id,
        ip=ip,
        user_agent=user_agent,
    )
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
