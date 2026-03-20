import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import StrEnum
from io import BytesIO
from typing import BinaryIO

from google.cloud.storage import Client  # type: ignore[import-untyped]
from loguru import logger
from PIL import Image, ImageOps

from core.common.utils import time_it
from core.config import GCP_PROJECT_ID, GCP_STORAGE_BUCKET

from ..exceptions import NotFoundError
from ..models import Character, EditEvent
from ..models.edit_event import EditEventStatus, OperationType, TargetType
from ..models.image import ImageFormat
from ..repository import Repository, RepositoryV2
from .dto_types import UploadReferenceImageDTO

client = Client(project=GCP_PROJECT_ID)


IMAGE_FORMAT_FILE_SUFFIX = "jpeg"
ORIGINAL_QUALITY = 90

THUMB_SIZE = (100, 100)
THUMB_QUALITY = 82

PREVIEW_SIZE = (500, 500)
PREVIEW_QUALITY = 85

CPU_COUNT = os.cpu_count() or 1
MAX_WORKERS = max(1, CPU_COUNT - 1)

_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


@dataclass(slots=True)
class ReadyToUploadImageDTO:
    width: int
    height: int
    size_bytes: int
    image_bytes: BytesIO
    content_type: ImageFormat


class ImageVariantKey(StrEnum):
    ORIGINAL = "original"
    THUMB = "thumb"
    PREVIEW = "preview"


ImageVariants = dict[ImageVariantKey, ReadyToUploadImageDTO]


class ImageUploadService:
    def __init__(self, repository: Repository, repository_v2: RepositoryV2):
        self.repository = repository
        self.repository_v2 = repository_v2
        self.bucket = client.bucket(GCP_STORAGE_BUCKET)

    async def upload_image(
        self,
        dto: UploadReferenceImageDTO,
    ) -> None:
        character = await self._get_authorized_character(dto)

        async with self.repository.db.begin():
            edit_event = await self._create_in_processing_edit_event(dto)

        object_key_prefix = self._build_object_key_prefix(dto, character.slug)
        image_variants = await self._create_image_variants(dto.image)
        self._upload_image_variants_to_bucket(object_key_prefix, image_variants)

        async with self.repository.db.begin():
            await self._mark_edit_event_completed(edit_event)

        # next steps:
        # - update tables
        # TODO continue with next steps
        return None

    async def _add_image_to_db(self) -> None:
        raise NotImplementedError("Not implemented")

    async def _create_in_processing_edit_event(
        self, dto: UploadReferenceImageDTO
    ) -> EditEvent:
        return await self.repository_v2.edit_event.create_edit_event(
            project_id=dto.project_id,
            target_type=TargetType.CHARACTER,
            target_id=dto.character_id,
            operation_type=OperationType.UPLOAD_REFERENCE_IMAGE,
            user_instruction="",
            input_snapshot=None,
        )

    async def _mark_edit_event_completed(self, edit_event: EditEvent) -> EditEvent:
        return await self.repository_v2.edit_event.update_edit_event(
            edit_event_id=edit_event.id,
            status=EditEventStatus.SUCCEEDED,
            output_snapshot=None,
        )

    async def _get_authorized_character(
        self, dto: UploadReferenceImageDTO
    ) -> Character:
        character = await self.repository_v2.character.get_character_for_user_in_project_and_story(
            dto.user_id, dto.project_id, dto.story_id, dto.character_id
        )
        if character is None:
            raise NotFoundError(
                f"Character {dto.character_id} not found in project {dto.project_id} and story {dto.story_id}"
            )
        return character

    def _build_object_key_prefix(
        self, dto: UploadReferenceImageDTO, character_slug: str
    ) -> str:
        return f"{dto.user_id}/character/{character_slug}/references/{dto.filename}"

    @time_it
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

        # build image variants
        image_variants = ImageVariants(
            {
                ImageVariantKey.ORIGINAL: original,
                ImageVariantKey.THUMB: thumb,
                ImageVariantKey.PREVIEW: preview,
            }
        )
        return image_variants

    def _pack_image_to_ready_to_upload_dto(
        self, image: Image.Image, quality: int
    ) -> ReadyToUploadImageDTO:
        width, height = image.size
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        size_bytes = buffer.tell()
        buffer.seek(
            0
        )  # Important: reset pointer to start of buffer, because save moves it to end
        return ReadyToUploadImageDTO(
            width, height, size_bytes, buffer, ImageFormat.JPEG
        )

    @time_it
    def _process_original_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        processed_img = ImageOps.exif_transpose(image=image.copy()).convert("RGB")
        return self._pack_image_to_ready_to_upload_dto(processed_img, ORIGINAL_QUALITY)

    @time_it
    def _create_thumb_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        thumb = image.copy()
        thumb.thumbnail(THUMB_SIZE)  # modifies in place
        return self._pack_image_to_ready_to_upload_dto(thumb, THUMB_QUALITY)

    @time_it
    def _create_preview_image(self, image: Image.Image) -> ReadyToUploadImageDTO:
        preview = image.copy()
        preview.thumbnail(PREVIEW_SIZE)  # modifies in place
        return self._pack_image_to_ready_to_upload_dto(preview, PREVIEW_QUALITY)

    @time_it
    def _upload_image_variants_to_bucket(
        self, object_key_prefix: str, image_variants: ImageVariants
    ) -> None:
        for key, value in image_variants.items():
            object_key = f"{object_key_prefix}/{key}.{IMAGE_FORMAT_FILE_SUFFIX}"
            self._upload_file_object_to_bucket(object_key, value)

        return None

    @time_it
    def _upload_file_object_to_bucket(
        self, object_key: str, upload_dto: ReadyToUploadImageDTO
    ) -> None:
        # we expect object_key_prefix to be the full prefix
        # .../thumb.jpeg
        blob = self.bucket.blob(object_key)
        try:
            blob.upload_from_file(
                upload_dto.image_bytes, content_type=upload_dto.content_type
            )
        except Exception as e:
            logger.error(f"Failed to upload image to bucket: {e}")
            raise e

    async def _create_image_artefact(self) -> None:
        raise NotImplementedError("Not implemented")
