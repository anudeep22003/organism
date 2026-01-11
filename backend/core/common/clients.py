import instructor
from openai import AsyncOpenAI

from core.config import OPENAI_API_KEY

async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
instructor_client = instructor.from_openai(async_openai_client)
