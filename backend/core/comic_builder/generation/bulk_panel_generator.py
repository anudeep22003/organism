import uuid
from typing import Awaitable, Callable

from ..state_manager import ProjectStateManager
from . import PanelRenderer


class BulkPanelGenerator:
    def __init__(self, state_manager: ProjectStateManager) -> None:
        self._state_manager = state_manager
        self._panel_generator = PanelRenderer(state_manager)

    async def execute(
        self,
        project_id: uuid.UUID,
        notify_callback: Callable[[], Awaitable[None]] | None = None,
    ) -> None:
        project = await self._state_manager.fetch_project(project_id)
        state = self._state_manager.get_validated_state(project)
        for panel in state.panels:
            await self._panel_generator.execute(project_id, panel)
            if notify_callback:
                await notify_callback()
