import json
from typing import Optional

from loguru import logger
from pydantic import Field

from core.sockets.types.envelope import AliasedBaseModel
from core.universe.events import get_current_timestamp

logger = logger.bind(name=__name__)



class TokenRecord(AliasedBaseModel):
    created_at: int = Field(default_factory=get_current_timestamp)
    expires_at: int
    user_id: Optional[str] = Field(default=None)


_VALID_TOKENS: dict[str, TokenRecord] = {}


def register_session_token(session_token: str, ttl_seconds: int, user_id: Optional[str] = None) -> None:
    expires_at = get_current_timestamp() + ttl_seconds * 1000
    token_record = TokenRecord(expires_at=expires_at, user_id=user_id)
    _VALID_TOKENS[session_token] = token_record
    write_tokens_to_file()
    logger.debug("Registered session token", token_record=token_record)


def write_tokens_to_file() -> None:
    with open("tokens.json", "w") as f:
        json.dump({k: v.model_dump() for k, v in _VALID_TOKENS.items()}, f, indent=4)


def verify_session_token(session_token: str) -> bool:
    logger.debug("Verifying session token", session_token=session_token)
    token_record = _VALID_TOKENS.get(session_token)
    if token_record is None:
        logger.debug("Invalid session token", session_token=session_token)
        return False
    if token_record.expires_at < get_current_timestamp():
        logger.debug("Session token expired", session_token=session_token)
        return False
    return True


def revoke_session_token(session_token: str) -> None:
    _VALID_TOKENS.pop(session_token)
    write_tokens_to_file()
    logger.debug("Revoked session token", session_token=session_token)
