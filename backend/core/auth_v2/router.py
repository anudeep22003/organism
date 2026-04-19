from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from loguru import logger

from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth", "google-auth"])


oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_oauth_client_id,
    client_secret=settings.google_oauth_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "access_type": "offline",  # request refresh token (for future Google API use)
        "prompt": "consent",  # ensure refresh token is returned
    },
)


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    google = oauth.create_client("google")
    redirect_uri = str(request.url_for("callback"))
    # The callback URL is the endpoint that Google will redirect the user to after they complete authentication.
    # Here, request.url_for("callback") dynamically generates the absolute URL for the "/callback" route,
    # ensuring that OAuth will return the authenticated user to the correct handler in this FastAPI app.
    logger.info(f"Redirecting to Google OAuth: {redirect_uri}")
    return await google.authorize_redirect(request, redirect_uri)  # type: ignore[no-any-return]


@router.get("/callback", response_model=dict)
async def callback() -> dict:
    return {}


@router.get("/me", response_model=dict)
async def me() -> dict:
    return {}
