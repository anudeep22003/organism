import asyncio
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import Field

from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_seconds

logger = logger.bind(name=__name__)

router = APIRouter(prefix="/comic-builder", tags=["comic", "builder"])


class SimpleEnvelope(AliasedBaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(default_factory=get_current_timestamp_seconds)

    request_id: str | None = None
    stream_id: str | None = None
    seq: int | None = None

    data: dict


async def stream_dummy_story() -> AsyncGenerator[str, None]:
    TIME_TO_SLEEP = 0.1
    story = "Once upon a time, there was a cat who went to the store and bought a fish."
    # start event
    yield (
        SimpleEnvelope(
            data={"delta": "start"},
        ).model_dump_json()
        + "\n"
    )

    for word in story.split():
        yield (
            SimpleEnvelope(
                data={"delta": word},
            ).model_dump_json()
            + "\n"
        )
        await asyncio.sleep(TIME_TO_SLEEP)

    yield (
        SimpleEnvelope(
            data={"finish_reason": "stop"},
        ).model_dump_json()
        + "\n"
    )


@router.post("/story")
async def build_comic_story() -> StreamingResponse:
    return StreamingResponse(content=stream_dummy_story())
