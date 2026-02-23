import uuid
from typing import Literal

from pydantic import Field

from core.common import AliasedBaseModel

StreamingStatus = Literal["idle", "streaming", "completed", "error"]


class BaseComicStateEntity(AliasedBaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_input_text: list[str] = Field(default_factory=list)
    status: StreamingStatus = Field(default="idle")
