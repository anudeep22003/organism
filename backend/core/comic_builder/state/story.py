from pydantic import Field

from .base import BaseComicStateEntity


class Story(BaseComicStateEntity):
    story_text: str = Field(default="")

