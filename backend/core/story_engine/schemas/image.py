import uuid
from datetime import datetime

from core.common import AliasedBaseModel


class ImageResponseSchema(AliasedBaseModel):
    id: uuid.UUID
    object_key: str
    bucket: str
    content_type: str
    width: int
    height: int
    size_bytes: int
    created_at: datetime


class ImageSignedUrlResponseSchema(AliasedBaseModel):
    url: str
    expires_at: datetime
