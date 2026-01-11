import uuid
from typing import Literal

from loguru import logger
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.common import AliasedBaseModel
from core.common.clients import instructor_client

from .models import Project
from .state import ComicState

logger = logger.bind(name=__name__)


class CharacterExtractorError(Exception):
    pass


class NoStoryError(CharacterExtractorError):
    pass


class NoStoryContentError(CharacterExtractorError):
    pass


class Character(AliasedBaseModel):
    """
    Character profile extracted from story, optimized for AI image generation.
    Works for humanoids, creatures, abstract concepts (emotions), and objects.
    Each field provides clear visual guidance for rendering.
    """

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
    def __init__(self, project_id: uuid.UUID, db: AsyncSession):
        self.project_id = project_id
        self._db = db
        logger.info(f"CharacterExtractor initialized for project {project_id}")

    async def load_memory(self) -> ComicState:
        logger.debug(f"Loading memory for project {self.project_id}")
        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            logger.error(f"Project with id {self.project_id} not found")
            raise ValueError(f"Project with id {self.project_id} not found")
        logger.debug(f"Memory loaded successfully for project {self.project_id}")
        return ComicState.model_validate(project.state)

    def extract_story(self, memory: ComicState) -> str:
        logger.debug(f"Extracting story from memory for project {self.project_id}")
        content = memory.phases[0].content
        if not content:
            logger.error(f"No story content found for project {self.project_id}")
            raise NoStoryContentError(
                f"No story content found for project {self.project_id}"
            )
        story = content.text
        if not story:
            logger.error(f"No story text found for project {self.project_id}")
            raise NoStoryError(f"No story found for project {self.project_id}")
        logger.debug(f"Story extracted successfully, length: {len(story)} chars")
        return story

    async def extract_characters(self, story: str) -> list[Character]:
        logger.info(
            f"Starting character extraction for project {self.project_id} "
            "(this may take a while...)"
        )
        logger.debug(f"Story length: {len(story)} chars")

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

        if not response:
            logger.error(f"No response from AI for project {self.project_id}")
            raise CharacterExtractorError(
                f"No characters found for project {self.project_id}"
            )

        characters = response.characters

        if not characters:
            logger.warning(
                f"AI returned empty character list for project {self.project_id}"
            )
            raise CharacterExtractorError(
                f"No characters found for project {self.project_id}"
            )

        logger.info(
            f"Extracted {len(characters)} characters: {[c.name for c in characters]}"
        )
        return characters

    def serialize_characters(self, characters: list[Character]) -> list[dict]:
        logger.debug(f"Serializing {len(characters)} characters")
        serialized = [character.model_dump() for character in characters]
        logger.debug("Characters serialized successfully")
        return serialized

    def validate_extract_character_phase(self, memory: ComicState) -> None:
        logger.debug(
            f"Validating extract character phase for project {self.project_id}"
        )
        if len(memory.phases) < 2:
            logger.error(
                f"Memory has only {len(memory.phases)} phases, expected at least 2"
            )
            raise CharacterExtractorError(
                f"Extract character phase not found for project {self.project_id}"
            )
        if not memory.phases[1].content:
            logger.error("Phase 1 content is missing")
            raise CharacterExtractorError(
                f"Extract character content not found for project {self.project_id}"
            )
        logger.debug("Extract character phase validation passed")

    def sync_characters_to_local_memory(
        self, characters: list[Character], memory: ComicState
    ) -> ComicState:
        logger.debug(f"Syncing {len(characters)} characters to local memory")

        try:
            self.validate_extract_character_phase(memory)
        except CharacterExtractorError as e:
            logger.error(f"Validation failed: {e}")
            raise CharacterExtractorError(
                f"Error validating extract character phase: {e}"
            ) from e

        serialized_characters = self.serialize_characters(characters)
        memory.phases[1].content.payload = serialized_characters  # type: ignore[union-attr]
        memory.current_phase_index = (
            1  # keep on current phase, and prevent from resetting to 0
        )

        logger.debug("Characters synced to local memory successfully")
        return memory

    async def sync_local_memory_to_db(self, memory: ComicState) -> None:
        logger.debug(f"Syncing local memory to database for project {self.project_id}")

        try:
            self.validate_extract_character_phase(memory)
        except CharacterExtractorError as e:
            logger.error(f"Validation failed before DB sync: {e}")
            raise CharacterExtractorError(
                f"Error validating extract character phase: {e}"
            ) from e

        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            logger.error(f"Project {self.project_id} not found during DB sync")
            raise ValueError(f"Project with id {self.project_id} not found")
        project.state = memory.model_dump()
        await self._db.commit()
        logger.info(
            f"Memory synced to database successfully for project {self.project_id}"
        )

    async def run_and_return_updated_state(self) -> ComicState:
        logger.info(
            f"Starting character extraction pipeline for project {self.project_id}"
        )

        memory = await self.load_memory()
        logger.debug("Step 1/4 complete: Memory loaded")

        story = self.extract_story(memory)
        logger.debug("Step 2/4 complete: Story extracted")

        characters = await self.extract_characters(story)
        logger.debug("Step 3/4 complete: Characters extracted")

        memory = self.sync_characters_to_local_memory(characters, memory)
        logger.debug("Step 4/4 complete: Characters synced to local memory")

        await self.sync_local_memory_to_db(memory)

        logger.info(
            f"Character extraction pipeline completed successfully "
            f"for project {self.project_id}"
        )
        return memory
