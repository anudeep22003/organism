import asyncio
from typing import Callable, NamedTuple

import fal_client
from fal_client.client import AnyJSON, Status

from core.config import settings

MAX_CONCURRENT_REQUESTS = 10


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


class ConcurrentMediaGenerator:
    def __init__(self) -> None:
        self._semaphore: asyncio.Semaphore | None = None
        self._client: fal_client.AsyncClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop_bound_state(
        self,
    ) -> tuple[asyncio.Semaphore, fal_client.AsyncClient]:
        """Return (semaphore, client) bound to the current running loop.

        A module-level singleton outlives any single event loop. In production
        there is exactly one loop for the lifetime of the process, so this
        creates once and reuses. In tests (per-function loops), it recreates on
        each new loop — no closed-loop errors, no leaked state.
        """
        loop = asyncio.get_running_loop()
        if self._loop is not loop:
            self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
            self._client = fal_client.AsyncClient(key=settings.fal_api_key)
            self._loop = loop
        assert self._semaphore is not None and self._client is not None
        return self._semaphore, self._client

    async def subscribe(
        self,
        arguments: dict,
        on_queue_update: Callable[[Status], None],
        model: ImageGenerationModel = DEFAULT_IMAGE_GENERATION_MODEL,
    ) -> AnyJSON:
        model_name, arguments = self._get_model_and_arguments(arguments, model)
        semaphore, client = self._get_loop_bound_state()
        async with semaphore:
            return await client.subscribe(
                model_name, arguments=arguments, on_queue_update=on_queue_update
            )

    def _get_model_and_arguments(
        self, arguments: dict, model: ImageGenerationModel
    ) -> tuple[str, dict]:
        number_of_characters_in_panel = len(arguments.get("image_urls", []))
        model_name = self._get_model_name(number_of_characters_in_panel, model)
        arguments = self._clean_arguments(arguments, number_of_characters_in_panel)
        return model_name, arguments

    def _get_model_name(
        self, number_of_characters_in_panel: int, model: ImageGenerationModel
    ) -> str:
        if number_of_characters_in_panel > 0:
            return model.edit_model
        return model.generation_model

    def _clean_arguments(
        self, arguments: dict, number_of_characters_in_panel: int
    ) -> dict:
        if number_of_characters_in_panel > 0:
            return arguments
        if "image_urls" in arguments:
            arguments.pop("image_urls")
        return arguments


fal_async_client = ConcurrentMediaGenerator()
