from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/google-auth", tags=["auth", "google-auth"])


class PlaceholderResponse(BaseModel):
    endpoint: Literal["login", "callback", "me"]
    status: Literal["NOT_IMPLEMENTED"]
    message: str


@router.get("/login", response_model=PlaceholderResponse)
async def login() -> PlaceholderResponse:
    return PlaceholderResponse(
        endpoint="login",
        status="NOT_IMPLEMENTED",
        message="google auth v2 login is not implemented yet",
    )


@router.get("/callback", response_model=PlaceholderResponse)
async def callback() -> PlaceholderResponse:
    return PlaceholderResponse(
        endpoint="callback",
        status="NOT_IMPLEMENTED",
        message="google auth v2 callback is not implemented yet",
    )


@router.get("/me", response_model=PlaceholderResponse)
async def me() -> PlaceholderResponse:
    return PlaceholderResponse(
        endpoint="me",
        status="NOT_IMPLEMENTED",
        message="google auth v2 me is not implemented yet",
    )
