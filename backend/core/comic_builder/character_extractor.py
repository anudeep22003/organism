import uuid
from typing import Literal

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.common import AliasedBaseModel
from core.services.intelligence import instructor_client

from .models import Project
from .state import ComicState


class CharacterExtractorError(Exception):
    pass


class NoStoryError(CharacterExtractorError):
    pass


class NoStoryContentError(CharacterExtractorError):
    pass


class Character(AliasedBaseModel):
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


class ExtractedCharacters(AliasedBaseModel):
    """Container for all characters extracted from a story."""

    characters: list[Character] = Field(
        ..., description="List of all significant characters found in the story."
    )


class CharacterExtractor:
    """Extracts and persists character profiles from story content via LLM."""

    def __init__(self, project_id: uuid.UUID, db: AsyncSession):
        self.project_id = project_id
        self._db = db

    async def load_memory(self) -> ComicState:
        """Fetch project state from database."""
        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        return ComicState.model_validate(project.state)

    def extract_story(self, memory: ComicState) -> str:
        """Pull story text from the first phase."""
        content = memory.phases[0].content
        if not content:
            raise NoStoryContentError(f"No story content for project {self.project_id}")
        if not content.text:
            raise NoStoryError(f"No story text for project {self.project_id}")
        return content.text

    async def extract_characters(self, story: str) -> list[Character]:
        """Use LLM to identify characters from story text."""
        response = await instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=ExtractedCharacters,
            messages=[
                {
                    "role": "system",
                    "content": "You are a comic book writer. You will be given a story and you will need to extract the characters from the story.",
                },
                {"role": "user", "content": story},
            ],
        )

        if not response or not response.characters:
            raise CharacterExtractorError(
                f"No characters found for project {self.project_id}"
            )

        return response.characters

    def serialize_characters(self, characters: list[Character]) -> list[dict]:
        """Convert character models to dicts for storage."""
        return [character.model_dump() for character in characters]

    def validate_extract_character_phase(self, memory: ComicState) -> None:
        """Ensure phase 1 exists and has content."""
        if len(memory.phases) < 2:
            raise CharacterExtractorError(
                f"Phase 1 missing for project {self.project_id}"
            )
        if not memory.phases[1].content:
            raise CharacterExtractorError(
                f"Phase 1 content missing for project {self.project_id}"
            )

    def sync_characters_to_local_memory(
        self, characters: list[Character], memory: ComicState
    ) -> ComicState:
        """Write extracted characters into memory state."""
        self.validate_extract_character_phase(memory)
        memory.phases[1].content.payload = self.serialize_characters(characters)  # type: ignore[union-attr]
        memory.current_phase_index = 1
        return memory

    async def sync_local_memory_to_db(self, memory: ComicState) -> None:
        """Persist updated memory state to database."""
        self.validate_extract_character_phase(memory)
        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        project.state = memory.model_dump()
        await self._db.commit()

    async def run_and_return_updated_state(self) -> ComicState:
        """Execute full extraction pipeline: load → extract → persist."""
        memory = await self.load_memory()
        story = self.extract_story(memory)
        characters = await self.extract_characters(story)
        memory = self.sync_characters_to_local_memory(characters, memory)
        await self.sync_local_memory_to_db(memory)
        return memory
