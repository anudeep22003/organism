import uuid
from typing import Any, Literal

from pydantic import Field

from core.common import AliasedBaseModel

StreamingStatus = Literal["idle", "streaming", "completed", "error"]


class BaseComicStateEntity(AliasedBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_input_text: list[str] = Field(default_factory=list)
    status: StreamingStatus = Field(default="idle")


class Artifact(BaseComicStateEntity):
    url: str | None = None


class Story(BaseComicStateEntity):
    story_text: str = Field(default="")


class Character(BaseComicStateEntity):
    name: str
    brief: str
    character_type: Literal["humanoid", "creature", "concept", "object"]
    era: str
    visual_form: str
    color_palette: str
    distinctive_markers: str
    demeanor: str
    role: Literal["protagonist", "antagonist", "supporting", "minor"]
    render: Artifact | None = None


class ComicPanel(BaseComicStateEntity):
    image_url: str
    text: str
    characters: list[uuid.UUID]
    background: str
    foreground: str
    border: str
    shadow: str
    glow: str
    render: Artifact | None = None


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
