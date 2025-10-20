from fastapi import APIRouter
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
async def login(request: LoginRequest) -> LoginResponse:
    logger.debug(f"Login request: {request}")
    return LoginResponse(valid=True, session_id="123")
