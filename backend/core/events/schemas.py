import uuid
from typing import Any

from core.common import AliasedBaseModel

from .models import AggregateType, EventType


class EmitEventSchema(AliasedBaseModel):
    event_type: EventType
    aggregate_type: AggregateType
    aggregate_id: uuid.UUID
    payload: dict[str, Any]


class UserCreatedEventPayload(AliasedBaseModel):
    user_id: uuid.UUID
