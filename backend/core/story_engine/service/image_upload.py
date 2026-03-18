from io import BytesIO

from fastapi import UploadFile
from google.cloud.storage import Client  # type: ignore[import-untyped]

from core.config import GCP_PROJECT_ID, GCP_STORAGE_BUCKET

from ..exceptions import NotFoundError
from ..models import Character
from ..models.edit_event import OperationType, TargetType
from ..repository import Repository
from .dto_types import UploadReferenceImageDTO

client = Client(project=GCP_PROJECT_ID)


class ImageUploadService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.bucket = client.bucket(GCP_STORAGE_BUCKET)

    async def upload_image(
        self,
        dto: UploadReferenceImageDTO,
    ) -> None:
        character = await self._get_authorized_character(dto)
        await self._create_in_processing_edit_event(dto)
        _ = self._create_object_key(dto, character.slug)

        # next steps:
        # - create thumb, preview and original options using Pillow bufio
        # - upload to google storage
        # - update tables

    async def _create_in_processing_edit_event(
        self, dto: UploadReferenceImageDTO
    ) -> None:
        await self.repository.create_edit_event(
            project_id=dto.project_id,
            target_type=TargetType.CHARACTER,
            target_id=dto.character_id,
            operation_type=OperationType.UPLOAD_REFERENCE_IMAGE,
            user_instruction="",
            input_snapshot=None,
        )

    async def _get_authorized_character(
        self, dto: UploadReferenceImageDTO
    ) -> Character:
        character = await self.repository.get_character_for_user_in_project_and_story(
            dto.user_id, dto.project_id, dto.story_id, dto.character_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {dto.character_id} not found in project {dto.project_id} and story {dto.story_id}"
            )
        return character

    def _create_object_key(
        self, dto: UploadReferenceImageDTO, character_slug: str
    ) -> str:
        return f"{dto.user_id}/character-references/{character_slug}"

    def _create_image_variants(self) -> dict[str, BytesIO]:
        # create thumb, preview and original options using Pillow
        # do we send byte array?
        # cheap way to get size
        # buf.seek(0, 2)     # move head to end
        # size = buf.tell()  # head position == size
        # buf.seek(0)        # rewind for upload
        raise NotImplementedError("Not implemented")

    def _upload_image_to_bucket(self, image: UploadFile) -> str:
        raise NotImplementedError("Not implemented")

    async def _create_image_artefact(self) -> None:
        raise NotImplementedError("Not implemented")

    async def _mark_edit_event_completed(self) -> None:
        raise NotImplementedError("Not implemented")
