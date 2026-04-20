import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from loguru import logger

from core.config import settings

from ..config import REFRESH_TOKEN_COOKIE_NAME
from ..exceptions import InvalidRefreshTokenError, UserNotFoundError
from ..schemas import UserResponse
from ..services import AuthService
from .cookies import clear_auth_cookies, set_auth_cookies
from .dependencies import (
    get_auth_service,
    get_current_user_id_v2,
    get_request_client_context,
)
from .oauth_client import oauth

router = APIRouter(prefix="/auth", tags=["auth", "google-auth"])


def _frontend_auth_redirect(path: str) -> str:
    frontend_base_url = settings.frontend_url or settings.cors_origins
    return f"{frontend_base_url.rstrip('/')}{path}"


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    google = oauth.create_client("google")
    redirect_uri = str(request.url_for("callback"))
    logger.info(f"Redirecting to Google OAuth: {redirect_uri}")
    return await google.authorize_redirect(  # type: ignore[no-any-return]
        request,
        redirect_uri,
        access_type="offline",
        prompt="consent",
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
        set_auth_cookies(
            response,
            access_token=result.tokens.access_token,
            refresh_token=result.tokens.refresh_token,
        )
        return response
    except Exception as exc:
        logger.error(f"Error authorizing access token: {exc}")
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
    set_auth_cookies(
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
    clear_auth_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
