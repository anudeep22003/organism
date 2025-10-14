import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request, Response
from pydantic import Field

from core.sockets.types.envelope import AliasedBaseModel

router = APIRouter(prefix="/session")


class Session(AliasedBaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sids: set[str] = Field(default_factory=set)


sessions: dict[str, Session] = {}


class CreateSessionResponse(AliasedBaseModel):
    message: str
    session_id: str


@router.post("/create")
async def create_session(response: Response) -> CreateSessionResponse:
    session_id = str(uuid.uuid4())
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,  # prevent javascript access
        secure=True,  # only send cookie over HTTPS
        samesite="lax",
        max_age=3600,  # 1 hour
        path="/",
    )
    return CreateSessionResponse(message="session created", session_id=session_id)


class ValidateSessionResponse(AliasedBaseModel):
    valid: bool
    message: str


@router.get("/validate")
async def validate_session(request: Request) -> ValidateSessionResponse:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        return ValidateSessionResponse(
            valid=False, message="No session found in cookies"
        )
    if session_id not in sessions:
        return ValidateSessionResponse(
            valid=False,
            message="session found in cookies, but no active session with this id found.",
        )
    return ValidateSessionResponse(valid=True, message="session validated")


class DestroySessionResponse(AliasedBaseModel):
    message: str
    session_id: str


@router.post("/destroy")
async def destroy_session(request: Request) -> dict[str, str]:
    session_id = request.cookies.get("session_id")
    if session_id is None:
        return {"message": "No session found in cookies"}
    if session_id not in sessions:
        return {
            "message": "session found in cookies, but no active session with this id found."
        }
    session = sessions[session_id]
    session.sids.clear()
    del sessions[session_id]
    return {"message": "session destroyed", "session_id": session_id}
