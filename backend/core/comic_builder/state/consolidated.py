import uuid
from typing import Any

from pydantic import Field

from core.common import AliasedBaseModel

from .character import Character
from .panel import ComicPanel
from .story import Story


class ConsolidatedComicState(AliasedBaseModel):
    story: Story
    characters: dict[uuid.UUID, Character] = Field(default_factory=dict)
    panels: list[ComicPanel] = Field(default_factory=list)


def initialize_empty_consolidated_state_dict() -> dict[str, Any]:
    return ConsolidatedComicState(
        story=Story(),
        characters={},
        panels=[],
    ).model_dump(by_alias=True)

