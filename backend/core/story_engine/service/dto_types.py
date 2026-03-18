import uuid

from fastapi import UploadFile

from core.common import AliasedBaseModel


class UploadReferenceImageDTO(AliasedBaseModel):
    user_id: str
    project_id: uuid.UUID
    story_id: uuid.UUID
    character_id: uuid.UUID
    image: UploadFile
