import textwrap
import uuid
from typing import Any, AsyncGenerator, AsyncIterator

from openai.types.chat import ChatCompletionChunk

from core.services.intelligence.clients import async_openai_client

from ..exceptions import StoryGeneratorError
from ..state_manager import ProjectStateManager


class StoryStreamGenerator:
    """Low-level LLM streaming - pure generation, no state awareness."""

    async def stream(self, prompt: str) -> AsyncIterator[ChatCompletionChunk]:
        """Stream story chunks from LLM."""
        return await async_openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            temperature=0.7,
        )

    def _system_prompt(self) -> str:
        return textwrap.dedent("""
            You are a story teller.
            You understand the hero's journey and how to mould it to the story at play.
            You are a lover and a fighter, you understand the power of story to change the world.
            You know where to start the story, how to build tension, how to resolve the story, and how to keep the reader engaged.
            You are a master of the story arc, you know how to create a story that is both engaging and satisfying.
            You are a master at both telling fictionalized and real life stories.
            For real life stories you know to be faithful to history or mythology but are adept at knowing which creative liberties to take so that the original story and/or the feelings it evokes are still captured.
        """).strip()


class StoryPhase:
    """Phase coordinator for story generation - matches other phase signatures."""

    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager
        self._generator = StoryStreamGenerator()

    async def execute_streaming(
        self, project_id: uuid.UUID, prompt: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute story generation with streaming output.

        Yields dicts suitable for SimpleEnvelope.data field.
        Persists story to state on completion.
        """
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)

        accumulated: list[str] = []
        try:
            stream = await self._generator.stream(prompt)
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                accumulated.append(delta or "")
                yield {"delta": delta}

                if chunk.choices[0].finish_reason is not None:
                    state.story.story_text = "".join(accumulated)
                    await self._state_manager.sync_state(project, state)
                    yield {"finish_reason": chunk.choices[0].finish_reason}
                    break
        except Exception as e:
            raise StoryGeneratorError(
                f"Story generation failed for project {project_id}"
            ) from e
