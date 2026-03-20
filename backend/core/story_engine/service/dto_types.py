import uuid
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(slots=True)
class UploadReferenceImageDTO:
    user_id: str
    project_id: uuid.UUID
    story_id: uuid.UUID
    character_id: uuid.UUID
    image: BinaryIO
    filename: str
