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


class CharacterBase(AliasedBaseModel):
    """Character profile optimized for AI image generation."""

    name: str = Field(
        ...,
        description="The character's name or title as it appears in the story.",
    )

    brief: str = Field(
        ...,
        description="A one-sentence summary of who/what this character is and their role in the story.",
    )

    character_type: Literal["humanoid", "creature", "concept", "object"] = Field(
        ...,
        description=(
            "The fundamental nature of this character. "
            "'humanoid' for humans/human-like beings, "
            "'creature' for animals/monsters/non-human entities, "
            "'concept' for abstract ideas personified (emotions, forces, ideas like Jealousy or Time), "
            "'object' for inanimate things with character (a sentient sword, talking car)."
        ),
    )

    era: str = Field(
        ...,
        description=(
            "The time period or aesthetic context that influences visual style. "
            "Examples: 'Victorian England 1880s', 'Modern day 2020s', 'Feudal Japan 1600s', "
            "'Cyberpunk 2080', 'Ancient Rome 50 BC', 'timeless/mythological', 'cellular/microscopic'. "
            "This determines overall visual aesthetics, clothing for humanoids, or stylistic rendering for concepts."
        ),
    )

    visual_form: str = Field(
        ...,
        description=(
            "Complete visual description of what this character looks like. "
            "For humanoids: age, gender presentation, build, face, hair, skin tone, typical clothing. "
            "For creatures: body structure, size, texture, limbs, features. "
            "For concepts: the visual metaphor or form it takes (e.g., 'a shadowy figure with green-tinged edges', "
            "'a swirling vortex of amber light'). "
            "For objects: shape, size, material, condition. "
            "Be specific and vivid - this is the primary image generation prompt."
        ),
    )

    color_palette: str = Field(
        ...,
        description=(
            "The dominant colors associated with this character. "
            "Examples: 'deep greens and blacks with gold accents', 'warm oranges fading to red', "
            "'clinical whites and steel grays', 'iridescent purple and blue'. "
            "Crucial for visual consistency across panels."
        ),
    )

    distinctive_markers: str = Field(
        ...,
        description=(
            "Unique visual elements that make this character instantly recognizable across panels. "
            "Examples: 'a scar across left eyebrow', 'glowing red eyes', 'trailing wisps of smoke', "
            "'a cracked surface', 'always surrounded by small floating particles'. "
            "Use 'none' if no distinctive markers."
        ),
    )

    demeanor: str = Field(
        ...,
        description=(
            "How the character moves, carries itself, or feels - affects pose and mood in images. "
            "Examples: 'confident and imposing', 'nervous and flickering', 'serene and floating', "
            "'chaotic and unpredictable', 'slow and deliberate'."
        ),
    )

    role: Literal["protagonist", "antagonist", "supporting", "minor"] = Field(
        ...,
        description="The character's narrative importance in the story.",
    )


class Character(BaseComicStateEntity, CharacterBase):
    render: Artifact | None = None


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
