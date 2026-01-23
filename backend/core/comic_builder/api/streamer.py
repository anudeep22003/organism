import textwrap
import uuid
from typing import AsyncGenerator, AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from pydantic import Field

from core.common import AliasedBaseModel
from core.common.utils import get_current_timestamp_seconds
from core.config import OPENAI_API_KEY

logger = logger.bind(name=__name__)

router = APIRouter(tags=["comic", "builder"])


class SimpleEnvelope(AliasedBaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: int = Field(default_factory=get_current_timestamp_seconds)

    request_id: str | None = None
    stream_id: str | None = None
    seq: int | None = None

    data: dict


async def enveloped_stream(
    stream: AsyncIterator[ChatCompletionChunk],
) -> AsyncGenerator[str, None]:
    async for chunk in stream:
        yield (
            SimpleEnvelope(
                data={"delta": chunk.choices[0].delta.content},
            ).model_dump_json()
            + "\n"
        )

        if chunk.choices[0].finish_reason is not None:
            yield (
                SimpleEnvelope(
                    data={"finish_reason": chunk.choices[0].finish_reason},
                ).model_dump_json()
                + "\n"
            )
            break


async def create_stream(user_prompt: str) -> AsyncIterator[ChatCompletionChunk]:
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    stream = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": textwrap.dedent(
                    """
                    You are a story teller.
                    You understand the hero's journey and how to mould it to the story at play.
                    You are a lover and a fighter, you understand the power of story to change the world.
                    You know where to start the story, how to build tension, how to resolve the story, and how to keep the reader engaged.
                    You are a master of the story arc, you know how to create a story that is both engaging and satisfying.
                    You are a master at both telling fictionalized and real life stories.
                    For real life stories you know to be faithful to history or mythology but are adept at knowing which creative liberties to take so that the original story and/or the feelings it evokes are still captured.
                    """
                ),
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        stream=True,
        temperature=0.7,
    )
    return stream


class ComicBuilderRequest(AliasedBaseModel):
    story_prompt: str


@router.post("/story")
async def build_comic_story(request: ComicBuilderRequest) -> StreamingResponse:
    user_prompt = request.story_prompt
    return StreamingResponse(content=enveloped_stream(await create_stream(user_prompt)))
