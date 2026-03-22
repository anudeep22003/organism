"""
Integration tests for ImageUploadService.upload_reference_image.

Both tests are real end-to-end: real DB, real GCS bucket, real image processing.
Fixtures (user → project → story → character) are created fresh per test and
torn down automatically by conftest.py.

Manual setup before running:
1. Ensure .env.local has valid DATABASE_URL and GCP credentials.
2. Ensure GCP_STORAGE_BUCKET is accessible with your active credentials.
3. Run with: pytest -m "manual and integration" tests/story_engine/test_image_upload_service.py

Set DELETE_TEST_UPLOADS_AFTER_TEST = True to clean GCS objects after each test.
Image DB rows are always deleted after each test so the fixture chain can
tear down the character → story → project → user FK chain cleanly.
"""

import os
from io import BytesIO

import pytest
from google.cloud.storage import Client  # type: ignore[import-untyped]
from google.cloud.storage.bucket import Bucket  # type: ignore[import-untyped]
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.config import GCP_PROJECT_ID, GCP_STORAGE_BUCKET
from core.story_engine.models import (
    Character,
    EditEvent,
    EditEventStatus,
    Project,
    Story,
)
from core.story_engine.models import Image as ImageModel
from core.story_engine.models.edit_event import EditEventTargetType
from core.story_engine.models.image import ImageDiscriminatorKey
from core.story_engine.repository import RepositoryV2
from core.story_engine.service.image.service import ImageUploadService

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DELETE_TEST_UPLOADS_AFTER_TEST = False

QUALITY = 95
SIDE = 2600

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_test_jpeg_stream() -> BytesIO:
    img = Image.frombytes("RGB", (SIDE, SIDE), os.urandom(SIDE * SIDE * 3))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
    buffer.seek(0)
    return buffer


def _gcs_bucket() -> "Bucket":
    return Client(project=GCP_PROJECT_ID).bucket(GCP_STORAGE_BUCKET)


async def _delete_image_rows(
    db_session: AsyncSession, character: Character
) -> list[str]:
    """Delete image rows for this character and return their object_keys for GCS cleanup."""
    result = await db_session.execute(
        select(ImageModel).where(ImageModel.character_id == character.id)
    )
    images = list(result.scalars().all())
    object_keys = [img.object_key for img in images]
    await db_session.execute(
        delete(ImageModel).where(ImageModel.character_id == character.id)
    )
    await db_session.commit()
    return object_keys


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_reference_image_via_service(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Calling ImageUploadService directly writes one image row and one blob."""
    repo = RepositoryV2(db_session)
    service = ImageUploadService(db=db_session, repository_v2=repo)
    object_keys: list[str] = []

    try:
        await service.upload_reference_image(
            user_id=str(user.id),
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
            image_byte_stream=_build_test_jpeg_stream(),
        )

        # --- DB: image row ---
        result = await db_session.execute(
            select(ImageModel).where(
                ImageModel.project_id == project.id,
                ImageModel.character_id == character.id,
            )
        )
        images = list(result.scalars().all())

        assert len(images) == 1
        image = images[0]
        assert image.discriminator_key == ImageDiscriminatorKey.CHARACTER_REFERENCE
        assert image.object_key.startswith(
            f"{user.id}/character/{character.slug}/references/"
        )
        assert image.bucket == GCP_STORAGE_BUCKET
        assert image.width > 0
        assert image.height > 0
        assert image.size_bytes > 0

        # --- GCS: blob exists ---
        blob = _gcs_bucket().blob(image.object_key)
        assert blob.exists()
        blob.reload()
        assert blob.size is not None
        assert blob.size > 0

    finally:
        object_keys = await _delete_image_rows(db_session, character)
        if DELETE_TEST_UPLOADS_AFTER_TEST:
            bucket = _gcs_bucket()
            for key in object_keys:
                bucket.blob(key).delete()


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_reference_image_via_endpoint(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """POSTing to the upload endpoint writes one image row, one blob, and a
    SUCCEEDED edit event."""
    object_keys: list[str] = []

    try:
        access_token = JWTTokenManager().create_access_token(str(user.id))
        url = (
            f"/api/comic-builder/v2/project/{project.id}"
            f"/story/{story.id}"
            f"/character/{character.id}/upload-reference-image"
        )
        headers = {"Authorization": f"Bearer {access_token}"}
        files = {"image": ("test-upload.jpg", _build_test_jpeg_stream(), "image/jpeg")}

        response = await api_client.post(url, headers=headers, files=files)
        assert response.status_code == 200

        # --- DB: image row ---
        result = await db_session.execute(
            select(ImageModel).where(
                ImageModel.project_id == project.id,
                ImageModel.character_id == character.id,
            )
        )
        images = list(result.scalars().all())

        assert len(images) == 1
        image = images[0]
        assert image.discriminator_key == ImageDiscriminatorKey.CHARACTER_REFERENCE
        assert image.object_key.startswith(
            f"{user.id}/character/{character.slug}/references/"
        )
        assert image.bucket == GCP_STORAGE_BUCKET
        assert image.width > 0
        assert image.height > 0
        assert image.size_bytes > 0

        # --- DB: edit event ---
        event_result = await db_session.execute(
            select(EditEvent)
            .where(
                EditEvent.project_id == project.id,
                EditEvent.target_id == character.id,
                EditEvent.target_type == EditEventTargetType.CHARACTER,
            )
            .order_by(EditEvent.created_at.desc())
            .limit(1)
        )
        event = event_result.scalar_one_or_none()
        assert event is not None
        assert event.status == EditEventStatus.SUCCEEDED

        # --- GCS: blob exists ---
        blob = _gcs_bucket().blob(image.object_key)
        assert blob.exists()
        blob.reload()
        assert blob.size is not None
        assert blob.size > 0

    finally:
        object_keys = await _delete_image_rows(db_session, character)
        if DELETE_TEST_UPLOADS_AFTER_TEST:
            bucket = _gcs_bucket()
            for key in object_keys:
                bucket.blob(key).delete()
