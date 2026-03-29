import instructor
from openai import AsyncOpenAI

from core.config import settings

async_openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
instructor_client = instructor.from_openai(async_openai_client)
