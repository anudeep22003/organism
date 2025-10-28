import secrets
from typing import Optional

from fastapi import APIRouter, Cookie, Request, Response
from loguru import logger

from core.auth.token_manager import register_session_token, verify_session_token
from core.sockets.types.envelope import AliasedBaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

TTL_SECONDS = 120  # 2 minutes

logger = logger.bind(name=__name__)


class LoginRequest(AliasedBaseModel):
    email: str
    password: str


class LoginResponse(AliasedBaseModel):
    valid: bool
    session_id: str


@router.post("/login")
async def login(
    response: Response,
    request: Request,
    body: LoginRequest,
    session_token: Optional[str] = Cookie(None),
) -> LoginResponse:
    if session_token is not None and verify_session_token(session_token):
        logger.debug(
            "Session token found in cookies and is valid", session_token=session_token
        )
        return LoginResponse(valid=True, session_id=session_token)
    logger.debug(
        "No session token found in cookies, generating new one and sending to client"
    )
    session_token = secrets.token_urlsafe(32)
    ttl_seconds = 1200
    register_session_token(session_token, ttl_seconds)

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600,
        path="/",
    )
    return LoginResponse(valid=True, session_id=session_token)
