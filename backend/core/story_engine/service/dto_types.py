import uuid
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(slots=True)
class ProjectUserCharacterDTO:
    user_id: str
    project_id: uuid.UUID
    story_id: uuid.UUID
    character_id: uuid.UUID


@dataclass(slots=True)
class FileToUploadDTO:
    file: BinaryIO
    filename: str


@dataclass(slots=True)
class UploadReferenceImageDTO:
    file_to_upload: FileToUploadDTO
    project_user_character: ProjectUserCharacterDTO
