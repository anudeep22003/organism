import textwrap
import uuid

from pydantic import Field

from core.common import AliasedBaseModel
from core.services.intelligence import instructor_client

from ..exceptions import NoStoryError, PanelGeneratorError
from ..state import ComicPanel, ComicPanelBase, ConsolidatedComicState
from ..state_manager import ProjectStateManager


class PanelsGeneratorResponse(AliasedBaseModel):
    panels: list[ComicPanelBase] = Field(
        ...,
        description="The panels generated for the story.",
    )


class PanelGenerator:
    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager

    async def execute(self, project_id: uuid.UUID) -> None:
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)
        story = self._extract_story_text(state)
        panels = await self._generate_panel(story)
        new_state = self._build_new_state_with_panels(panels, state)
        await self._state_manager.sync_state(project, new_state)

    def _extract_story_text(self, state: ConsolidatedComicState) -> str:
        if not state.story.story_text:
            raise NoStoryError("No story available for project. Generate story first.")
        return state.story.story_text

    def _system_prompt(self) -> str:
        return textwrap.dedent("""
        You are a comic book writer. 
        You are an expert at taking a story and breaking it down into comic panels.
        Given the story below, generate a list of comic panels for the story.
        Each panel should be a single page in the comic book. 
        Each panel should have a background, characters, and dialogue.
        The characters should be the names of the characters in the panel. 
        The dialogue should be the dialogue in the panel and should include who the speaker is.
        The background should be a description of the background of the panel. 
        The panels should be in the order of the story.
        """)

    async def _generate_panel(self, story: str) -> PanelsGeneratorResponse:
        try:
            response = await instructor_client.chat.completions.create(
                model="gpt-4o",
                response_model=PanelsGeneratorResponse,
                messages=[
                    {
                        "role": "system",
                        "content": self._system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": f"Story:\n\n{story}\n\nPlease generate a list of comic panels for the story.",
                    },
                ],
            )
        except Exception as e:
            raise PanelGeneratorError(f"Error generating panel: {e}") from e
        return response

    def _build_new_state_with_panels(
        self, panels: PanelsGeneratorResponse, state: ConsolidatedComicState
    ) -> ConsolidatedComicState:
        completed_panels = [
            ComicPanel(**panel.model_dump(), status="completed")
            for panel in panels.panels
        ]
        new_state = state.model_copy(update={"panels": completed_panels})
        return new_state
