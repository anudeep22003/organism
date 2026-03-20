"""
Integration test for ImageUploadService.upload_image with real GCS writes.

Manual setup (edit these constants before running):
1) Ensure the IDs map to a real user/project/story/character in your local DB.
2) Ensure your Google credentials are active for the configured bucket.
3) Run only this test when you intentionally want real bucket writes.
"""

import os
import time
import uuid
from io import BytesIO
from types import SimpleNamespace, TracebackType
from typing import cast

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.config import GCP_STORAGE_BUCKET
from core.story_engine.models import EditEvent
from core.story_engine.models import Image as ImageModel
from core.story_engine.models.edit_event import (
    EditEventStatus,
    OperationType,
    TargetType,
)
from core.story_engine.models.image import ImageVariant
from core.story_engine.repository import RepositoryV2
from core.story_engine.service.dto_types import (
    FileToUploadDTO,
    ProjectUserCharacterDTO,
    UploadReferenceImageDTO,
)
from core.story_engine.service.image_upload import ImageUploadService, client
from core.story_engine.service.upload_filename import build_upload_reference_filename

# Manual config values - replace with real IDs before running.
USER_ID = "2c2af68f-9315-4bab-8aa3-3b1a581dca8e"
PROJECT_ID = uuid.UUID("9c10291d-4b0a-4c2f-8deb-417d36a12d7b")
STORY_ID = uuid.UUID("0a358afa-670c-4729-b1d3-838a76320993")
CHARACTER_ID = uuid.UUID("61c317cf-06c9-4d95-bd06-6d9518a4eeba")
CHARACTER_SLUG = "the-sprite"
FILENAME_PREFIX = "integration-upload"


QUALITY = 95
SIDE = 2600

DELETE_TEST_UPLOADS_AFTER_TEST = False


def _build_test_jpeg_stream() -> BytesIO:
    img = Image.frombytes("RGB", (SIDE, SIDE), os.urandom(SIDE * SIDE * 3))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
    buffer.seek(0)
    return buffer


class StubRepository:
    class _TxContext:
        async def __aenter__(self) -> None:
            return None

        async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc: BaseException | None,
            tb: TracebackType | None,
        ) -> bool:
            return False

    class _DB:
        def begin(self) -> "StubRepository._TxContext":
            return StubRepository._TxContext()

    def __init__(self) -> None:
        self.db = StubRepository._DB()

    async def get_character_for_user_in_project_and_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> SimpleNamespace:
        return SimpleNamespace(slug=CHARACTER_SLUG)


class StubRepositoryV2EditEvent:
    async def create_edit_event(
        self,
        *,
        project_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        operation_type: str,
        user_instruction: str,
        input_snapshot: dict[str, object] | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(id=uuid.uuid4())

    async def update_edit_event(
        self,
        *,
        edit_event_id: uuid.UUID,
        status: str,
        output_snapshot: dict[str, object] | None = None,
    ) -> SimpleNamespace:
        return SimpleNamespace(id=edit_event_id, status=status)


class StubRepositoryV2Character:
    async def get_character_for_user_in_project_and_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> SimpleNamespace:
        return SimpleNamespace(slug=CHARACTER_SLUG)


class StubRepositoryV2:
    def __init__(self) -> None:
        self.edit_event = StubRepositoryV2EditEvent()
        self.character = StubRepositoryV2Character()


def _build_candidate_keys(
    object_key_prefix: str, variant_key: ImageVariant
) -> list[str]:
    # Current implementation appends only "." after the key.
    # Keep .jpeg candidate too so this test survives the expected key-format fix.
    return [
        f"{object_key_prefix}/{variant_key}.jpeg",
    ]


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_image_uploads_all_variants_to_bucket() -> None:
    service = ImageUploadService(
        db=cast("AsyncSession", StubRepository._DB()),
        repository_v2=cast(RepositoryV2, StubRepositoryV2()),
    )
    filename = f"{FILENAME_PREFIX}-{int(time.time())}"
    dto = UploadReferenceImageDTO(
        file_to_upload=FileToUploadDTO(
            file=_build_test_jpeg_stream(), filename=filename
        ),
        project_user_character=ProjectUserCharacterDTO(
            user_id=USER_ID,
            project_id=PROJECT_ID,
            story_id=STORY_ID,
            character_id=CHARACTER_ID,
        ),
    )
    object_key_prefix = f"{dto.project_user_character.user_id}/character/{CHARACTER_SLUG}/references/{dto.file_to_upload.filename}"

    uploaded_keys: list[str] = []
    try:
        await service.upload_image(dto)

        for variant_key in (
            ImageVariant.ORIGINAL,
            ImageVariant.THUMB,
            ImageVariant.PREVIEW,
        ):
            matching_key: str | None = None
            for candidate_key in _build_candidate_keys(object_key_prefix, variant_key):
                blob = service.bucket.blob(candidate_key)
                if blob.exists():
                    matching_key = candidate_key
                    blob.reload()  # Refresh metadata to get accurate size
                    assert blob.size is not None
                    assert blob.size > 0
                    break
            assert matching_key is not None, (
                f"Expected uploaded object for {variant_key} under prefix {object_key_prefix}"
            )
            uploaded_keys.append(matching_key)
    finally:
        if DELETE_TEST_UPLOADS_AFTER_TEST:
            for key in uploaded_keys:
                service.bucket.blob(key).delete()


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_reference_image_endpoint_side_effects(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    filename = f"{FILENAME_PREFIX}-endpoint-{int(time.time())}"
    request_filename = f"{filename}.jpg"
    stored_filename = build_upload_reference_filename(request_filename)
    access_token = JWTTokenManager().create_access_token(USER_ID)
    url = (
        f"/api/comic-builder/v2/project/{PROJECT_ID}"
        f"/story/{STORY_ID}"
        f"/character/{CHARACTER_ID}/upload-reference-image"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    files = {"image": (request_filename, _build_test_jpeg_stream(), "image/jpeg")}

    created_image_ids: list[uuid.UUID] = []
    created_object_keys: list[str] = []

    try:
        response = await api_client.post(url, headers=headers, files=files)
        assert response.status_code == 200
        assert response.content in (b"", b"null")

        image_query = await db_session.execute(
            select(ImageModel).where(
                ImageModel.project_id == PROJECT_ID,
                ImageModel.character_id == CHARACTER_ID,
                ImageModel.filename == stored_filename,
            )
        )
        created_images = list(image_query.scalars().all())
        assert len(created_images) == 3
        assert {image.variant for image in created_images} == {
            ImageVariant.ORIGINAL.value,
            ImageVariant.THUMB.value,
            ImageVariant.PREVIEW.value,
        }

        object_key_prefix = (
            f"{USER_ID}/character/{CHARACTER_SLUG}/references/{stored_filename}"
        )
        for image in created_images:
            created_image_ids.append(image.id)
            created_object_keys.append(image.object_key)

            assert image.image_type == "character_reference"
            assert image.bucket == GCP_STORAGE_BUCKET
            assert image.object_key.startswith(object_key_prefix)
            assert image.width > 0
            assert image.height > 0
            assert image.size_bytes > 0

        bucket = client.bucket(GCP_STORAGE_BUCKET)
        for object_key in created_object_keys:
            blob = bucket.blob(object_key)
            assert blob.exists()
            blob.reload()
            assert blob.size is not None
            assert blob.size > 0

        event_query = await db_session.execute(
            select(EditEvent)
            .where(
                EditEvent.project_id == PROJECT_ID,
                EditEvent.target_id == CHARACTER_ID,
                EditEvent.target_type == TargetType.CHARACTER.value,
                EditEvent.operation_type == OperationType.UPLOAD_REFERENCE_IMAGE.value,
            )
            .order_by(EditEvent.created_at.desc())
            .limit(1)
        )
        latest_event = event_query.scalar_one_or_none()
        assert latest_event is not None
        assert latest_event.status == EditEventStatus.SUCCEEDED.value
    finally:
        if DELETE_TEST_UPLOADS_AFTER_TEST:
            bucket = client.bucket(GCP_STORAGE_BUCKET)
            for object_key in created_object_keys:
                blob = bucket.blob(object_key)
                if blob.exists():
                    blob.delete()

            if created_image_ids:
                await db_session.execute(
                    delete(ImageModel).where(ImageModel.id.in_(created_image_ids))
                )
                await db_session.commit()
