import logging
import textwrap
import uuid
from typing import cast

from core.services.intelligence.media_generator import fal_async_client as client

from ..exceptions import RenderError
from ..state import Artifact, Character, ConsolidatedComicState
from ..state_manager import ProjectStateManager

logger = logging.getLogger(__name__)


class CharacterRenderer:
    """Renders character images via external image generation service."""

    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager

    async def execute(self, project_id: uuid.UUID, character: Character) -> None:
        """Execute full render pipeline: fetch -> render -> update -> sync."""
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)
        render_response = await self._render_character(character)
        image_url = self._get_character_url_from_response(render_response)
        updated_character = self._update_character_with_url(character, image_url)
        state = self._add_character_to_state(state, updated_character)
        await self._state_manager.sync_state(project, state)

    async def _render_character(self, character: Character) -> dict:
        """Call external service to generate character image."""
        prompt = self.build_character_render_prompt(character)
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

    def _get_character_url_from_response(self, response: dict) -> str:
        """Extract image URL from render response."""
        image_url = cast(str, response.get("images", [])[0].get("url"))
        if not image_url:
            logger.error(f"No image URL found in response: {response}")
            raise ValueError("No image URL found in response")
        return image_url

    def _update_character_with_url(self, character: Character, url: str) -> Character:
        """Create new character instance with render artifact."""
        render_artifact = Artifact(url=url)
        return character.model_copy(update={"render": render_artifact})

    def _add_character_to_state(
        self, state: ConsolidatedComicState, character: Character
    ) -> ConsolidatedComicState:
        """Add or update character in state."""
        state.characters[character.id] = character
        return state

    def build_character_render_prompt_advanced(self, character: Character) -> str:
        """Build detailed model-sheet style prompt for character rendering."""
        markers = character.distinctive_markers.strip()
        markers_line = (
            f"- Distinctive markers (must be present and clearly visible): {markers}"
            if markers and markers.lower() not in {"none", "n/a", ""}
            else "- Distinctive markers: none"
        )

        # Layout & guardrails depend on character type
        if character.character_type == "humanoid":
            layout_block = (
                "Comic book character model sheet / turnaround.\n"
                "Layout: square 1:1. Two full-body views of the SAME character: "
                "(1) front view (2) side profile view.\n"
                "Pose: neutral relaxed stance, arms at sides, neutral expression.\n"
                "Match scale and proportions between the two views. Clear spacing."
            )
            guardrails = (
                "Guardrails:\n"
                "- Keep identity consistent across both views (same face, hair, outfit, markers).\n"
                "- No dramatic pose, no extreme camera angle."
            )

        elif character.character_type == "creature":
            layout_block = (
                "Comic book creature model sheet / turnaround.\n"
                "Layout: square 1:1. Two full-body views of the SAME creature: "
                "(1) front view (2) side profile view.\n"
                "Pose: neutral stance, non-aggressive unless specified.\n"
                "Match scale and proportions between the two views. Clear spacing."
            )
            guardrails = (
                "Guardrails:\n"
                "- Emphasize anatomy, limbs, and silhouette clarity.\n"
                "- Keep creature features consistent between the two views."
            )

        elif character.character_type == "concept":
            layout_block = (
                "Comic book CONCEPT ENTITY design sheet (abstract character, non-humanoid).\n"
                "Layout: square 1:1. Show the same concept in two consistent manifestations:\n"
                "(A) primary full-form manifestation\n"
                "(B) alternate manifestation OR close-up detail view emphasizing the core motif.\n"
                "The two manifestations must clearly be the SAME entity (shared motif, palette, markers)."
            )
            guardrails = (
                "Guardrails for concept entities:\n"
                "- Do NOT turn this into a human/person unless explicitly described in the visual form.\n"
                "- Avoid human anatomy, clothing, or humanoid facial structure unless required.\n"
                "- Preserve abstraction: emphasize metaphor, energy form, symbolic geometry, particles, atmosphere."
            )

        else:  # object
            layout_block = (
                "Comic book OBJECT CHARACTER design sheet.\n"
                "Layout: square 1:1. Two views of the SAME object character: "
                "(1) front view (2) side or 3/4 view.\n"
                "Maintain object identity, shape, and material. Match scale between views."
            )
            guardrails = (
                "Guardrails for objects:\n"
                "- Only add a face/eyes/limbs if explicitly included in the visual form.\n"
                "- Keep materials, wear, and distinctive details consistent."
            )

        prompt = f"""
        Comic book character extraction render (clean reference design).

        {layout_block}

        Background: transparent background (PNG cutout), no environment, no props, no background gradients.

        Lighting & rendering: consistent neutral studio lighting, readable silhouette, crisp inks,
        clean linework, high detail, controlled cel shading, high-resolution.

        Character design:
        - Era / aesthetic context: {character.era}
        - Visual form (primary design): {character.visual_form}
        - Color palette: {character.color_palette}
        {markers_line}
        - Demeanor / motion feeling: {character.demeanor}

        {guardrails}

        Style: modern comic book illustration, sharp line art, subtle halftone texture.

        Avoid: text, logos, watermarks, speech bubbles, extra characters, scene/background,
        extreme foreshortening, dramatic shadows, camera tilt.
        """.strip()

        return textwrap.dedent(prompt)

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

