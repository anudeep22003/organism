import logging
import textwrap
import uuid
from typing import cast

import fal_client
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.comic_builder.models import Project
from core.config import FAL_API_KEY

from .consolidated_state import Artifact, Character, ConsolidatedComicState
from .exceptions import ComicBuilderError

logger = logging.getLogger(__name__)


class RenderError(ComicBuilderError):
    """External image generation failed."""

    pass


class CharacterRenderer:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def execute_render_character_pipeline(
        self, project_id: uuid.UUID, character: Character
    ) -> None:
        project = await self._fetch_project(project_id)
        state = self.get_validated_state(project)
        render_response = await self.render_character(character)
        image_url = self.get_character_url_from_response(render_response)
        updated_character = self.update_character_with_url(character, image_url)
        state = self.add_new_character_to_state(state, updated_character)
        await self.sync_state_to_project(project, state)

    async def _fetch_project(self, project_id: uuid.UUID) -> Project:
        """Fetch project within this session to ensure proper tracking."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} unexpctednly not found")
        return project

    async def sync_state_to_project(
        self, project: Project, state: ConsolidatedComicState
    ) -> None:
        project.state = state.model_dump()
        await self.db.commit()

    def get_validated_state(self, project: Project) -> ConsolidatedComicState:
        if not project.state:
            raise ValueError("Project state unexpctedly not initialized")
        return ConsolidatedComicState.model_validate(project.state)

    async def render_character(self, character: Character) -> dict:
        prompt = self.build_character_render_prompt(character)
        client = fal_client.AsyncClient(key=FAL_API_KEY)
        try:
            response = await client.subscribe(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": prompt,
                },
                on_queue_update=lambda status: print(f"Status: {status}"),
            )
            logger.info(f"Response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error rendering character: {e}")
            raise RenderError(f"Failed to render character {character.id}") from e

    def get_character_url_from_response(self, response: dict) -> str:
        image_url = cast(str, response.get("images", [])[0].get("url"))
        if not image_url:
            logger.error(f"No image URL found in response: {response}")
            raise ValueError("No image URL found in response")
        return image_url

    def update_character_with_url(self, character: Character, url: str) -> Character:
        render_artifact = Artifact(url=url)
        new_character = character.model_copy(update={"render": render_artifact})
        return new_character

    def add_new_character_to_state(
        self, state: ConsolidatedComicState, character: Character
    ) -> ConsolidatedComicState:
        state.characters[character.id] = character
        return state

    def build_character_render_prompt(self, character: Character) -> str:
        markers = character.distinctive_markers.strip()
        markers_line = (
            f"- Distinctive markers (must be present and clearly visible): {markers}"
            if markers and markers.lower() not in {"none", "n/a"}
            else "- Distinctive markers: none"
        )

        type_hint = {
            "humanoid": "human/humanoid anatomy, full body visible",
            "creature": "creature design, full body visible, clear anatomy and silhouette",
            "concept": "personified abstract entity, readable form, full body visible",
            "object": "anthropomorphized object, readable shape and materials, full body visible",
        }.get(character.character_type, "full body visible")

        prompt = f"""Comic book character model sheet / turnaround.

        Layout: square 1:1. Two full-body views of the SAME character: (1) front view (2) side profile view.
        Both views standing in a neutral relaxed stance, arms at sides, neutral expression.
        Match scale and proportions between the two views. Centered, clear spacing.

        Background: transparent background (PNG cutout), no environment, no props, no background gradients, no cast shadow on the background.

        Lighting & rendering: consistent neutral studio lighting across both views, readable silhouette,
        crisp inks, clean linework, high detail, controlled cel shading.

        Character design:
        - Era / aesthetic context: {character.era}
        - Character type guidance: {type_hint}
        - Visual form: {character.visual_form}
        - Color palette: {character.color_palette}
        {markers_line}
        - Demeanor: {character.demeanor} (subtle; keep pose neutral)

        Style: modern comic book illustration, sharp line art, subtle halftone texture, high-resolution character render.

        Avoid: text, logos, watermarks, speech bubbles, extra characters, busy effects, extreme foreshortening,
        dramatic shadows, camera tilt.
        """
        return textwrap.dedent(prompt).strip()
