"""Generate a name and description for a comic story from its metadata.

Uses gpt-4o-mini with instructor structured output — fast and cheap.
The LLM call is non-fatal: callers receive None on any failure.
"""

import json

from loguru import logger
from pydantic import BaseModel, Field

from core.services.intelligence import instructor_client
from core.services.intelligence.models import ModelsEnum


class StoryIdentity(BaseModel):
    """Generate a name and description for a comic story based on its metadata.

    The name should be evocative and concise — not a literal restatement of the
    source material title. The description should read like a creative brief:
    who the story is for, its emotional tone, visual style, and setting.
    """

    name: str = Field(
        ...,
        description=(
            "A short, evocative title for the comic story. "
            "Maximum 8 words. No quotes, no punctuation at the end. "
            "Should reflect the tone, setting, or emotional core — "
            "not merely echo the source material title."
        ),
        max_length=100,
    )

    description: str = Field(
        ...,
        description=(
            "One to two sentences describing what this comic will be about. "
            "Weave in the setting, emotional tone, comic style, and intended audience "
            "where relevant. Written as a creative brief, not a plot summary. "
            "Do not start with 'This comic'."
        ),
        max_length=300,
    )


async def generate_story_identity(meta: dict) -> tuple[str, str] | None:
    """Return (name, description) generated from story metadata, or None on failure.

    Never raises — any exception is logged and swallowed so story creation
    succeeds regardless of LLM availability.
    """
    if not meta:
        return None

    try:
        identity = await instructor_client.chat.completions.create(
            model=ModelsEnum.GPT_4O_MINI.value,
            response_model=StoryIdentity,
            max_retries=2,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Generate a name and description for a comic story "
                        "based on the following metadata:\n\n"
                        f"{json.dumps(meta, indent=2)}"
                    ),
                }
            ],
        )
        return identity.name, identity.description
    except Exception as exc:
        logger.warning(
            f"Story identity generation failed — story will have null name/description: {exc}"
        )
        return None
