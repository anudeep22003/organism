import datetime
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from typing import BinaryIO

import google.auth
from google.auth.transport.requests import Request
from google.cloud.storage import Client  # type: ignore[import-untyped]
from loguru import logger
from PIL import Image as PILImage
from PIL import ImageOps
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.story_engine.models.image import ImageDiscriminatorKey

from ..exceptions import NotFoundError, UploadImageError
from ..models import (
    Character,
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
    ImageContentType,
    Panel,
)
from ..models import (
    Image as ImageModel,
)
from ..repository import Repository
from ..storage_keys import character_reference_key, panel_reference_key

ORIGINAL_QUALITY = 90
IMAGE_FORMAT = "jpeg"
IMAGE_CONTENT_TYPE = ImageContentType.JPEG
SIGNED_URL_EXPIRY_MINUTES = 60


def extract_image_dimensions(image_bytes: BytesIO) -> tuple[int, int]:
    """Read width and height from image bytes using PIL header parsing.

    Only the image header is read (lazy open) — no full pixel decode.
    Resets the stream position to 0 after reading so the caller can
    pass the same BytesIO straight to GCS upload.

    Raises PIL.UnidentifiedImageError (or similar) if the bytes are not
    a valid image — callers should let this propagate so the edit event
    is marked FAILED rather than storing 0×0 dimensions silently.
    """
    img = PILImage.open(image_bytes)
    width, height = img.width, img.height
    image_bytes.seek(0)
    return width, height


@dataclass(slots=True)
class StorageReceipt:
    object_key: str
    bucket: str


@dataclass(slots=True)
class ProcessedImage:
    width: int
    height: int
    size_bytes: int
    image_bytes: BinaryIO
    content_type: ImageContentType


class ImageService:
    def __init__(self, db: AsyncSession, repository: Repository):
        self.db = db
        self.repository = repository
        self.gcs_upload_service = get_gcs_upload_service()
        self.image_processor = ImageProcessor()

    async def _upload_reference_image_core(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        target_id: uuid.UUID,
        target_type: EditEventTargetType,
        discriminator_key: ImageDiscriminatorKey,
        key_builder: Callable[[uuid.UUID], str],
        image_byte_stream: BinaryIO,
    ) -> ImageModel:
        """Generic reference-image upload: process bytes, upload to GCS, persist Image row.

        key_builder receives the edit_event_id once it exists and returns the
        GCS object key — this ensures every reference image key is traceable
        to its edit event, consistent with render key behaviour.
        """
        edit_event = EditEvent.create_edit_event(
            project_id=project_id,
            target_type=target_type,
            target_id=target_id,
            operation_type=EditEventOperationType.UPLOAD_REFERENCE_IMAGE,
            user_instruction="",
            input_snapshot=None,
            status=EditEventStatus.PENDING,
        )
        await self.repository.edit_event.add_edit_event_to_db(edit_event)
        await self.db.flush()
        edit_event_id = edit_event.id
        object_storage_key = key_builder(edit_event_id)
        processed_images = self.image_processor.process(image_byte_stream)

        image_models_to_create: list[ImageModel] = []
        for processed_image in processed_images:
            storage_receipt = self.gcs_upload_service.upload(
                object_storage_key,
                processed_image.image_bytes,
                processed_image.content_type,
            )
            image_model = ImageModel.create(
                project_id=project_id,
                user_id=user_id,
                target_id=target_id,
                width=processed_image.width,
                height=processed_image.height,
                content_type=processed_image.content_type,
                object_key=storage_receipt.object_key,
                bucket=storage_receipt.bucket,
                size_bytes=processed_image.size_bytes,
                discriminator_key=discriminator_key,
                meta={},
            )
            image_models_to_create.append(image_model)

        for image_model in image_models_to_create:
            await self.repository.image.create_image(image_model)
        await self.db.flush()
        first_image = image_models_to_create[0]
        await self.repository.edit_event.update_edit_event(
            edit_event_id=edit_event_id,
            status=EditEventStatus.SUCCEEDED,
            output_snapshot={"image_id": str(first_image.id)},
        )
        await self.db.commit()
        await self.db.refresh(first_image)
        return first_image

    async def upload_character_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
        image_byte_stream: BinaryIO,
    ) -> ImageModel:
        character = await self._get_authorized_character(
            user_id, project_id, story_id, character_id
        )
        return await self._upload_reference_image_core(
            user_id=user_id,
            project_id=project_id,
            target_id=character_id,
            target_type=EditEventTargetType.CHARACTER,
            discriminator_key=ImageDiscriminatorKey.CHARACTER_REFERENCE,
            key_builder=lambda eid: character_reference_key(
                user_id, project_id, story_id, character.slug, eid
            ),
            image_byte_stream=image_byte_stream,
        )

    async def upload_panel_reference_image(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
        image_byte_stream: BinaryIO,
    ) -> ImageModel:
        await self._get_authorized_panel(user_id, project_id, story_id, panel_id)
        return await self._upload_reference_image_core(
            user_id=user_id,
            project_id=project_id,
            target_id=panel_id,
            target_type=EditEventTargetType.PANEL,
            discriminator_key=ImageDiscriminatorKey.PANEL_REFERENCE,
            key_builder=lambda eid: panel_reference_key(
                user_id, project_id, story_id, panel_id, eid
            ),
            image_byte_stream=image_byte_stream,
        )

    async def get_character_reference_images(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> list[ImageModel]:
        await self._get_authorized_character(
            user_id, project_id, story_id, character_id
        )
        return await self.repository.image.get_character_reference_images(character_id)

    async def get_signed_url(
        self,
        image_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> tuple[str, datetime.datetime]:
        image = await self.repository.image.get_image(image_id)
        if image is None or image.user_id != user_id:
            raise NotFoundError(f"Image {image_id} not found")
        url, expires_at = self.gcs_upload_service.generate_signed_url(image.object_key)
        return url, expires_at

    async def _get_authorized_character(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> Character:
        character = (
            await self.repository.character.get_character_for_user_in_project_and_story(
                user_id, project_id, story_id, character_id
            )
        )
        if character is None:
            raise NotFoundError(
                f"Character {character_id} not found in project {project_id} and story {story_id}"
            )
        return character

    async def _get_authorized_panel(
        self,
        user_id: uuid.UUID,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        panel_id: uuid.UUID,
    ) -> Panel:
        """Verify the story exists in the project, then verify the panel belongs to that story."""
        story = await self.repository.story.get_story(project_id, story_id)
        if story is None:
            raise NotFoundError(f"Story {story_id} not found in project {project_id}")
        panel = await self.repository.panel.get_panel(panel_id, story_id)
        if panel is None:
            raise NotFoundError(f"Panel {panel_id} not found in story {story_id}")
        return panel


class ImageProcessor:
    def __init__(self) -> None:
        pass

    def process(self, image_byte_stream: BinaryIO) -> list[ProcessedImage]:
        img_bytes = image_byte_stream.read()
        original_image = PILImage.open(BytesIO(img_bytes))
        original_image_processed = self._process_original_image(original_image)
        return list([original_image_processed])

    def _process_original_image(self, image: PILImage.Image) -> ProcessedImage:
        processed_image = ImageOps.exif_transpose(image=image.copy()).convert("RGB")
        buffer = BytesIO()
        processed_image.save(
            buffer, format=IMAGE_FORMAT, quality=ORIGINAL_QUALITY, optimize=True
        )
        size_bytes = buffer.tell()
        buffer.seek(0)
        return ProcessedImage(
            width=processed_image.width,
            height=processed_image.height,
            size_bytes=size_bytes,
            image_bytes=buffer,
            content_type=ImageContentType.JPEG,
        )


class GCSUploadService:
    def __init__(self) -> None:
        # google.auth.default() resolves credentials from the environment:
        #   - Locally: picks up the JSON key file via GOOGLE_APPLICATION_CREDENTIALS.
        #              These are ServiceAccountCredentials — they hold a private key
        #              and implement google.auth.credentials.Signing directly.
        #   - Cloud Run: picks up the attached service account via the metadata server.
        #              These are ComputeEngine.Credentials — they hold only a token,
        #              NOT a private key. generate_signed_url() must therefore use
        #              the IAM signBlob API path (access_token + service_account_email).
        #
        # On Cloud Run, ADC provides tokens, not a local private key. Signed URL
        # generation therefore uses IAM-based signing (signBlob) — the SA needs
        # roles/iam.serviceAccountTokenCreator on itself (set in infra/iam.py).
        self.credentials, project_id = google.auth.default()
        self.client = Client(
            project=settings.gcp_project_id or project_id,
            credentials=self.credentials,
        )
        self.bucket = self.client.bucket(settings.gcp_storage_bucket)

    def upload(
        self, object_key: str, file_object: BinaryIO, content_type: ImageContentType
    ) -> StorageReceipt:
        try:
            blob = self.bucket.blob(object_key)
            blob.upload_from_file(file_object, content_type=content_type)
            return StorageReceipt(
                object_key=object_key, bucket=settings.gcp_storage_bucket
            )
        except Exception as e:
            logger.error(f"Failed to upload image to bucket: {object_key}, {e}")
            raise UploadImageError(
                f"Failed to upload image to bucket: {object_key}, {e}"
            ) from e

    def download_as_bytes(self, object_key: str) -> bytes:
        """Download a GCS blob as raw bytes. Synchronous — wrap in asyncio.to_thread."""
        return self.bucket.blob(object_key).download_as_bytes()  # type: ignore[no-any-return]

    def generate_signed_url(self, object_key: str) -> tuple[str, datetime.datetime]:
        expiry = datetime.timedelta(minutes=SIGNED_URL_EXPIRY_MINUTES)
        blob = self.bucket.blob(object_key)

        # Locally (ServiceAccountCredentials from JSON key file): credentials
        # implement google.auth.credentials.Signing, so generate_signed_url()
        # signs the URL locally with the private key — no extra args needed.
        #
        # On Cloud Run (ComputeEngine.Credentials): credentials hold only a
        # token, not a private key. We must use the IAM signBlob API path by
        # passing both access_token and service_account_email. The SDK branches
        # on `if access_token and service_account_email` to call signBlob via
        # the IAM Credentials API instead of credentials.sign_bytes().
        # Requires roles/iam.serviceAccountTokenCreator on the SA (iam.py).
        extra: dict = {}
        if not hasattr(self.credentials, "sign_bytes"):
            # Refresh to ensure token and service_account_email are populated.
            self.credentials.refresh(Request())
            extra = {
                "service_account_email": self.credentials.service_account_email,
                "access_token": self.credentials.token,
            }

        url = blob.generate_signed_url(
            expiration=expiry,
            method="GET",
            version="v4",
            **extra,
        )
        expires_at = datetime.datetime.now(datetime.timezone.utc) + expiry
        return url, expires_at


@lru_cache(maxsize=1)
def get_gcs_upload_service() -> GCSUploadService:
    """Return the process-wide GCSUploadService singleton.

    @lru_cache(maxsize=1) ensures the GCS client and its HTTP connection pool
    are created exactly once regardless of how many times this is called.
    Consistent with the _get_session_maker pattern in core/services/database.py.
    """
    return GCSUploadService()
