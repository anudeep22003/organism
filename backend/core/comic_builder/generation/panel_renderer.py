import uuid
from typing import NamedTuple, cast

from loguru import logger

from core.services.intelligence.media_generator import fal_async_client as client

from ..asset_manager import AssetManager
from ..exceptions import ComicBuilderError
from ..state import Artifact, ComicPanel, ConsolidatedComicState
from ..state_manager import ProjectStateManager

logger = logger.bind(name=__name__)


class ImageGenerationModel(NamedTuple):
    """Image generation model."""

    edit_model: str
    generation_model: str


nano_banana_pro = ImageGenerationModel(
    edit_model="fal-ai/nano-banana-pro/edit",
    generation_model="fal-ai/nano-banana-pro",
)

nano_banana = ImageGenerationModel(
    edit_model="fal-ai/nano-banana/edit",
    generation_model="fal-ai/nano-banana",
)

seedream = ImageGenerationModel(
    edit_model="fal-ai/bytedance/seedream/v4/edit",
    generation_model="fal-ai/bytedance/seedream/v4/text-to-image",
)

DEFAULT_IMAGE_GENERATION_MODEL = nano_banana


class PanelRenderError(ComicBuilderError):
    """Error rendering panel."""

    pass


class PanelRenderer:
    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager

    async def execute(self, project_id: uuid.UUID, panel: ComicPanel) -> None:
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)
        character_urls = self._get_character_urls(panel, state)
        render_response = await self._render_panel(panel, character_urls)
        image_url = self._get_panel_url_from_response(render_response)
        updated_panel = self._update_panel_with_url(panel, image_url)
        state = self._add_panel_to_state(state, updated_panel)
        await self._state_manager.sync_state(project, state)

    def _build_panel_render_prompt(self, panel: ComicPanel) -> str:
        """Build a prompt to render the panel."""
        return f"""
        Render a comic panel with the following features: 
        background: {panel.background} 
        characters: {panel.characters}
        dialogue: {panel.dialogue}

        Style: modern comic book illustration, sharp line art, subtle halftone texture, high detail, consistent lighting.
        Dialog bubble with the text of the dialogue should be placed above the characters and should be aligned with the characters.
        Do not obscure eyes or the face of the characters with the dialog bubble.
        """

    def _get_character_urls(
        self, panel: ComicPanel, state: ConsolidatedComicState
    ) -> list[str]:
        """Render panel with assets."""
        asset_manager = AssetManager(state)
        if not panel.characters:
            # support for scenes without characters
            return []
        character_urls = asset_manager.get_urls_for_characters(panel.characters)
        if not character_urls:
            logger.warning(
                "No character URLs found, rendering panel without passing characters..."
            )
            hit_rate = len(character_urls) / len(panel.characters) * 100

            logger.warning(
                f"Num of characters: {len(panel.characters)}, characters with urls: {character_urls}, hit rate: {hit_rate}%"
            )
        return character_urls

    def _get_render_model(self, character_urls: list[str]) -> str:
        """Get the model to use for rendering the panel."""
        characters_are_present = bool(character_urls)
        return (
            DEFAULT_IMAGE_GENERATION_MODEL.edit_model
            if characters_are_present
            else DEFAULT_IMAGE_GENERATION_MODEL.generation_model
        )

    def _get_render_arguments(
        self, panel: ComicPanel, character_urls: list[str]
    ) -> dict[str, str | list[str]]:
        """Get the render arguments to use for rendering the panel."""
        render_prompt = self._build_panel_render_prompt(panel)
        characters_are_present = bool(character_urls)

        if characters_are_present:
            return {
                "prompt": render_prompt,
                "image_urls": character_urls,
            }
        return {"prompt": render_prompt}

    async def _render_panel(self, panel: ComicPanel, character_urls: list[str]) -> dict:
        """Call external service to generate panel image."""
        render_arguments = self._get_render_arguments(panel, character_urls)
        model = self._get_render_model(character_urls)
        try:
            response = await client.subscribe(
                model,
                arguments=render_arguments,
                on_queue_update=lambda status: print(f"Status: {status}"),
            )
            logger.info(f"Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error rendering panel: {e}")
            raise PanelRenderError(f"Failed to render panel {panel.id}") from e

    def _get_panel_url_from_response(self, response: dict) -> str:
        """Extract image URL from render response."""
        image_url = cast(str, response.get("images", [])[0].get("url"))
        if not image_url:
            logger.error(f"No image URL found in response: {response}")
            # TODO change value error to FalResponseError? (also in character renderer)
            raise ValueError("No image URL found in response")
        return image_url

    def _update_panel_with_url(self, panel: ComicPanel, url: str) -> ComicPanel:
        """Create new panel instance with render artifact."""
        render_artifact = Artifact(url=url)
        return panel.model_copy(
            update={"render": render_artifact, "status": "completed"}
        )

    def _add_panel_to_state(
        self, state: ConsolidatedComicState, rendered_panel: ComicPanel
    ) -> ConsolidatedComicState:
        """Update panel in state."""
        new_panel_list = []

        for p in state.panels:
            if p.id == rendered_panel.id:
                new_panel_list.append(rendered_panel)
            else:
                new_panel_list.append(p)

        state.panels = new_panel_list
        return state
