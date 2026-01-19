import logging
import uuid
from typing import cast

import fal_client
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.comic_builder.models import Project
from core.config import FAL_API_KEY

from .consolidated_state import Artifact, Character, ConsolidatedComicState

logger = logging.getLogger(__name__)


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
            raise ValueError(f"Project {project_id} not found")
        return project

    async def sync_state_to_project(
        self, project: Project, state: ConsolidatedComicState
    ) -> None:
        project.state = state.model_dump()
        await self.db.commit()

    def get_validated_state(self, project: Project) -> ConsolidatedComicState:
        if not project.state:
            raise ValueError("Project state is not initialized")
        try:
            return ConsolidatedComicState.model_validate(project.state)
        except ValidationError as e:
            logger.error(f"Error validating project state: {e}")
            raise ValueError(f"Error validating project state: {e}")

    async def render_character(self, character: Character) -> dict:
        prompt = self.build_character_render_prompt(character)
        client = fal_client.AsyncClient(key=FAL_API_KEY)
        response = await client.subscribe(
            "fal-ai/flux/dev",
            arguments={
                "prompt": prompt,
            },
            on_queue_update=lambda status: print(f"Status: {status}"),
        )
        logger.info(f"Response: {response}")
        return response

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
        """Build an optimized image generation prompt from character data."""

        # Core visual description is the foundation
        prompt_parts: list[str] = [character.visual_form]

        # Era provides aesthetic context
        prompt_parts.append(f"{character.era} setting")

        # Color palette for visual consistency
        prompt_parts.append(f"color palette of {character.color_palette}")

        # Distinctive markers (skip if none)
        if character.distinctive_markers.lower() not in ("none", "n/a", ""):
            prompt_parts.append(character.distinctive_markers)

        # Demeanor affects pose/mood
        prompt_parts.append(f"{character.demeanor} expression and posture")

        # Character type can inform rendering style
        type_hints = {
            "humanoid": "detailed character portrait",
            "creature": "creature design, full body visible",
            "concept": "abstract personification, ethereal",
            "object": "anthropomorphized object, detailed rendering",
        }
        prompt_parts.append(
            type_hints.get(character.character_type, "character illustration")
        )

        # Style suffix
        prompt_parts.append("comic book art style, high detail, consistent lighting")

        return ", ".join(prompt_parts)
