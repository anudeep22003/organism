import secrets
from typing import Optional

from fastapi import APIRouter, Cookie, Request, Response
from loguru import logger

from core.sockets.types.envelope import AliasedBaseModel

router = APIRouter(prefix="/auth", tags=["auth"])


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
    if session_token is not None:
        logger.debug("Session token found in cookies", session_token=session_token)
        return LoginResponse(valid=True, session_id=session_token)
    logger.debug(
        "No session token found in cookies, generating new one and sending to client"
    )
    session_token = secrets.token_urlsafe(32)
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
