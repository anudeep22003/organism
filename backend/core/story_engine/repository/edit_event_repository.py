import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import EditEvent
from ..models.edit_event import EditEventStatus, OperationType
from .exception import NotFoundError


class EditEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_edit_event(
        self,
        project_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        operation_type: OperationType,
        user_instruction: str,
        input_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = EditEvent(
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            operation_type=operation_type.value,
            user_instruction=user_instruction,
            input_snapshot=input_snapshot,
        )
        self.db.add(event)
        return event

    async def update_edit_event(
        self,
        edit_event_id: uuid.UUID,
        status: EditEventStatus,
        output_snapshot: dict[str, Any] | None = None,
    ) -> EditEvent:
        event = await self.db.get(EditEvent, edit_event_id)
        if event is None:
            raise NotFoundError(f"EditEvent {edit_event_id} not found")

        event.status = status.value
        if output_snapshot is not None:
            event.output_snapshot = output_snapshot
        return event

    async def get_edit_events_for_target(
        self, target_type: str, target_id: uuid.UUID, limit: int = 20
    ) -> list[EditEvent]:
        stmt = (
            select(EditEvent)
            .where(
                EditEvent.target_type == target_type,
                EditEvent.target_id == target_id,
            )
            .order_by(desc(EditEvent.created_at))
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        events = result.scalars().all()
        return list(events)
