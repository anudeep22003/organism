from enum import Enum

import instructor
from openai import AsyncOpenAI

from core.config import settings


class OpenAIModel(Enum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_5 = "gpt-5"


async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
instructor_client = instructor.from_openai(async_openai_client)
