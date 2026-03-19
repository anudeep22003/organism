from dataclasses import dataclass
from io import BytesIO
from typing import BinaryIO

from google.cloud.storage import Client  # type: ignore[import-untyped]
from PIL import Image, ImageOps

from core.config import GCP_PROJECT_ID, GCP_STORAGE_BUCKET

from ..exceptions import NotFoundError
from ..models import Character
from ..models.edit_event import OperationType, TargetType
from ..repository import Repository
from .dto_types import UploadReferenceImageDTO

client = Client(project=GCP_PROJECT_ID)

THUMB_SIZE = (100, 100)
PREVIEW_SIZE = (500, 500)


@dataclass
class ReadyToUploadImageDTO:
    width: int
    height: int
    size_bytes: int
    image_bytes: BytesIO


@dataclass
class ImageVariants:
    original: ReadyToUploadImageDTO
    thumb: ReadyToUploadImageDTO
    preview: ReadyToUploadImageDTO


class ImageUploadService:
    def __init__(self, repository: Repository):
        self.repository = repository
        self.bucket = client.bucket(GCP_STORAGE_BUCKET)

    async def upload_image(
        self,
        dto: UploadReferenceImageDTO,
    ) -> tuple[str, ImageVariants]:
        character = await self._get_authorized_character(dto)
        await self._create_in_processing_edit_event(dto)
        object_key_prefix = self._create_object_key_prefix(dto, character.slug)
        image_variants = await self._create_image_variants(dto.image)

        # next steps:
        # - create thumb, preview and original options using Pillow bufio
        # - upload to google storage
        # - update tables
        # TODO continue with next steps
        return object_key_prefix, image_variants

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

    def _create_object_key_prefix(
        self, dto: UploadReferenceImageDTO, character_slug: str
    ) -> str:
        return f"{dto.user_id}/character/{character_slug}/references/"

    async def _create_image_variants(self, file_byte_stream: BinaryIO) -> ImageVariants:
        # read stream, get byte stream, create image and pass that forward
        # following methods create a copy before running any operations
        # To get size, you can buf.seek(2) and do a buf.tell() [2 is the end]
        # reading a buf, automatically moves the pointer to the end so doing a tell on it gives you the size in bytes
        # you could also look at length of the img_bytes
        # creating BytesIO(img_bytes) create a new cursor wiht its own local pointer on the same img_bytes
        img_bytes = file_byte_stream.read()
        base_image = Image.open(BytesIO(img_bytes))
        original = self._process_original_image(base_image)
        thumb = self._create_thumb_image(base_image)
        preview = self._create_preview_image(base_image)
        return ImageVariants(original, thumb, preview)

    def _pack_image_to_ready_to_upload_dto(
        self, image: Image.Image, quality: int
    ) -> ReadyToUploadImageDTO:
        width, height = image.size
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        size_bytes = buffer.tell()
        return ReadyToUploadImageDTO(width, height, size_bytes, buffer)

    def _process_original_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        processed_img = ImageOps.exif_transpose(image=image.copy()).convert("RGB")
        return self._pack_image_to_ready_to_upload_dto(processed_img, 90)

    def _create_thumb_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        thumb = image.copy()
        thumb.thumbnail(THUMB_SIZE)  # modifies in place
        return self._pack_image_to_ready_to_upload_dto(thumb, 90)

    def _create_preview_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE)  # modifies in place
        return self._pack_image_to_ready_to_upload_dto(preview, 90)

    def _upload_image_to_bucket(self) -> str:
        raise NotImplementedError("Not implemented")

    async def _create_image_artefact(self) -> None:
        raise NotImplementedError("Not implemented")

    async def _mark_edit_event_completed(self) -> None:
        raise NotImplementedError("Not implemented")
