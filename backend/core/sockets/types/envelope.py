import uuid
from datetime import datetime, timezone
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class AliasedBaseModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    def model_dump_json(self, **kwargs) -> str:
        return super().model_dump_json(by_alias=True, **kwargs)


class ErrorDetails(AliasedBaseModel):
    code: Literal[
        "E_INVALID",
        "E_UNAUTHORIZED",
        "E_FORBIDDEN",
        "E_NOT_FOUND",
        "E_CONFLICT",
        "E_RATE_LIMITED",
        "E_TIMEOUT",
        "E_OVERFLOW",
        "E_UNAVAILABLE",
        "E_INTERNAL",
    ]
    message: str
    details: dict | None = None


Direction = Literal["c2s", "s2c"]
Actor = Literal[
    "assistant", "coder", "writer", "claude", "scriptwriter", "director", "manager", "tasknotifier"
]
Action = Literal["stream"]
Modifier = Literal["start", "chunk", "end"]

T = TypeVar("T")


class Envelope(AliasedBaseModel, Generic[T]):
    # protocol
    v: str = "1"

    # identity & timing
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(
        default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000)
    )

    # correlation
    request_id: str | None = None  # requestId in TS
    stream_id: str | None = None  # streamId in TS
    seq: int | None = None  # per-stream sequence, starting at 1

    # control
    direction: Direction
    actor: Actor
    action: Action
    modifier: Modifier

    # payload
    data: T

    # errors
    error: ErrorDetails | None = None


class AckOk(AliasedBaseModel):
    ok: bool = True
    request_id: str
    stream_id: str


class Error(AliasedBaseModel):
    code: str
    message: str


class AckFail(AliasedBaseModel):
    ok: bool = False
    error: Error
