from pydantic import Field

from .artifact import Artifact
from .base import BaseComicStateEntity


class ComicPanelBase(BaseComicStateEntity):
    background: str = Field(
        ...,
        description="The background of the panel that will be rendered as a background image.",
    )
    characters: list[str] = Field(
        ..., description="The names of the characters in the panel."
    )
    dialogue: str = Field(
        ...,
        description="The dialogue in the panel that will be rendered as speech bubbles.",
    )


class ComicPanel(ComicPanelBase):
    render: Artifact | None = None
