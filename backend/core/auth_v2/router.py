from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from loguru import logger

from core.config import settings

from .api import get_auth_service
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
) -> RedirectResponse:
    try:
        google = oauth.create_client("google")
        token = await google.authorize_access_token(request)
        await service.handle_google_callback(token=token)
        return RedirectResponse(url=_frontend_auth_redirect("/auth/success"))
    except Exception as e:
        logger.error(f"Error authorizing access token: {e}")
        return RedirectResponse(url=_frontend_auth_redirect("/auth/failure"))
