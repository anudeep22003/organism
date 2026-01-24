import uuid

from pydantic import Field

from core.common import AliasedBaseModel
from core.services.intelligence import instructor_client

from ..exceptions import CharacterExtractorError, NoStoryError
from ..state import Character, CharacterBase, ConsolidatedComicState
from ..state_manager import ProjectStateManager


class ExtractedCharacters(AliasedBaseModel):
    """Container for all characters extracted from a story."""

    characters: list[CharacterBase] = Field(
        ..., description="List of all significant characters found in the story."
    )


class CharacterExtractor:
    """Extracts and persists character profiles from story content via LLM."""

    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager

    async def execute(self, project_id: uuid.UUID) -> ConsolidatedComicState:
        """Execute full extraction pipeline: load -> extract -> persist."""
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)
        story = self._extract_story(state, project_id)
        characters = await self._extract_characters_via_llm(story, project_id)
        state = self._sync_characters_to_state(characters, state)
        await self._state_manager.sync_state(project, state)
        return state

    def _extract_story(
        self, state: ConsolidatedComicState, project_id: uuid.UUID
    ) -> str:
        """Pull story text from the state."""
        if not state.story.story_text:
            raise NoStoryError(
                f"No story available for project {project_id}, generate story first"
            )
        return state.story.story_text

    async def _extract_characters_via_llm(
        self, story: str, project_id: uuid.UUID
    ) -> list[CharacterBase]:
        """Use LLM to identify characters from story text."""
        try:
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
        except Exception as e:
            raise CharacterExtractorError(
                f"LLM extraction failed for project {project_id}"
            ) from e

        if not response or not response.characters:
            raise CharacterExtractorError(
                f"No characters could be identified in your story for project {project_id}"
            )

        return response.characters

    def _sync_characters_to_state(
        self, characters: list[CharacterBase], state: ConsolidatedComicState
    ) -> ConsolidatedComicState:
        """Write extracted characters into state."""
        for character in characters:
            consolidated_character = Character(
                **character.model_dump(), status="completed"
            )
            state.characters[consolidated_character.id] = consolidated_character
        return state
