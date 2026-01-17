import uuid

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.common import AliasedBaseModel
from core.services.intelligence import instructor_client

from .consolidated_state import Character, CharacterBase, ConsolidatedComicState
from .models import Project


class CharacterExtractorError(Exception):
    pass


class NoStoryError(CharacterExtractorError):
    pass


class ExtractedCharacters(AliasedBaseModel):
    """Container for all characters extracted from a story."""

    characters: list[CharacterBase] = Field(
        ..., description="List of all significant characters found in the story."
    )


class CharacterExtractor:
    """Extracts and persists character profiles from story content via LLM."""

    def __init__(self, project_id: uuid.UUID, db: AsyncSession):
        self.project_id = project_id
        self._db = db

    async def load_memory(self) -> ConsolidatedComicState:
        """Fetch project state from database."""
        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        return ConsolidatedComicState.model_validate(project.state)

    def extract_story(self, memory: ConsolidatedComicState) -> str:
        """Pull story text from the first phase."""
        if not memory.story.story_text:
            raise NoStoryError(f"No story text for project {self.project_id}")
        return memory.story.story_text

    async def extract_characters(self, story: str) -> list[CharacterBase]:
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

    def sync_characters_to_local_memory(
        self, characters: list[CharacterBase], memory: ConsolidatedComicState
    ) -> ConsolidatedComicState:
        """Write extracted characters into memory state."""
        for character in characters:
            consolidated_character = Character(**character.model_dump())
            memory.characters[consolidated_character.id] = consolidated_character
        return memory

    async def sync_local_memory_to_db(self, memory: ConsolidatedComicState) -> None:
        """Persist updated memory state to database."""
        query = select(Project).where(Project.id == self.project_id)
        result = await self._db.execute(query)
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {self.project_id} not found")
        project.state = memory.model_dump()
        await self._db.commit()

    async def run_and_return_updated_state(self) -> ConsolidatedComicState:
        """Execute full extraction pipeline: load → extract → persist."""
        memory = await self.load_memory()
        story = self.extract_story(memory)
        characters = await self.extract_characters(story)
        memory = self.sync_characters_to_local_memory(characters, memory)
        await self.sync_local_memory_to_db(memory)
        return memory
