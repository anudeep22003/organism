from sqlalchemy.ext.asyncio import AsyncSession

from core.common.utils import get_current_datetime_utc
from core.events.dispatcher import DispatchEventForHandling, UpdateEventParams
from core.events.models import EventStatus

from .service import PaymentsService


class PaymentEventRetreivalError(Exception):
    """Error retreiving payment event."""

    pass


class PaymentsEventHandler:
    def __init__(self, db: AsyncSession) -> None:
        self.payments_service = PaymentsService(db)

    async def handle(
        self, dispatch_event_for_handling: DispatchEventForHandling
    ) -> None:
        event = await dispatch_event_for_handling.event_retreiver_fn(
            dispatch_event_for_handling.event_id
        )
        event_id = dispatch_event_for_handling.event_id
        payload = event.payload
        try:
            await self.payments_service.handle_create_customer(payload)
            updated_event_params = UpdateEventParams(
                event_id=event_id,
                status=EventStatus.COMPLETED,
                processed_at=get_current_datetime_utc(),
                claimed_at=get_current_datetime_utc(),
                failed_at=None,
                last_error=None,
            )
        except Exception as e:
            updated_event_params = UpdateEventParams(
                event_id=event_id,
                status=EventStatus.FAILED,
                processed_at=get_current_datetime_utc(),
                claimed_at=get_current_datetime_utc(),
                failed_at=get_current_datetime_utc(),
                last_error=str(e),
            )
        await dispatch_event_for_handling.confirm_handling_fn(
            event_id, updated_event_params
        )
