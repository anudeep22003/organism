"""
Integration tests for ImageUploadService.upload_reference_image.

Both tests are real end-to-end: real DB, real GCS bucket, real image processing.
Fixtures (user → project → story → character) are created fresh per test and
torn down automatically via ON DELETE CASCADE from the user delete in conftest.py.

Manual setup before running:
1. Ensure .env.local has valid DATABASE_URL and GCP credentials.
2. Ensure GCP_STORAGE_BUCKET is accessible with your active credentials.
3. Run with: pytest -m "manual and integration" tests/story_engine/test_image_upload_service.py

Set DELETE_TEST_UPLOADS_AFTER_TEST = True to also clean GCS objects after each test.
The GCS cleanup deletes everything under the test user's prefix — no orphaned folders.
"""

import os
from datetime import datetime, timezone
from io import BytesIO

import httpx
import pytest
from google.cloud.storage import Client  # type: ignore[import-untyped]
from google.cloud.storage.bucket import Bucket  # type: ignore[import-untyped]
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
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
from core.story_engine.service.image_service import ImageService

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DELETE_TEST_UPLOADS_AFTER_TEST = True

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


def _delete_gcs_prefix(user: User) -> None:
    """Delete all GCS objects under this test user's prefix."""
    bucket = _gcs_bucket()
    for blob in bucket.list_blobs(prefix=f"{user.id}/"):
        blob.delete()


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
    service = ImageService(db=db_session, repository_v2=repo)

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

    if DELETE_TEST_UPLOADS_AFTER_TEST:
        _delete_gcs_prefix(user)


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
    access_token = JWTTokenManager().create_access_token(str(user.id))
    url = (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{story.id}"
        f"/character/{character.id}/upload-reference-image"
    )
    headers = {"Authorization": f"Bearer {access_token}"}
    files = {"image": ("test-upload.jpg", _build_test_jpeg_stream(), "image/jpeg")}

    response = await api_client.post(url, headers=headers, files=files)
    assert response.status_code == 201

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

    if DELETE_TEST_UPLOADS_AFTER_TEST:
        _delete_gcs_prefix(user)


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(
    reason=(
        "Requires service account credentials with iam.serviceAccounts.signBlob permission. "
        "ADC user credentials cannot sign blobs. Set up a service account key first."
    )
)
async def test_get_signed_url_via_endpoint(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Uploading an image then requesting a signed URL returns a valid,
    accessible URL that expires in the future."""
    access_token = JWTTokenManager().create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {access_token}"}

    # Upload first to have an image to sign
    upload_url = (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{story.id}"
        f"/character/{character.id}/upload-reference-image"
    )
    upload_response = await api_client.post(
        upload_url,
        headers=headers,
        files={"image": ("test-upload.jpg", _build_test_jpeg_stream(), "image/jpeg")},
    )
    assert upload_response.status_code == 201
    image_id = upload_response.json()["id"]

    # Request signed URL
    signed_url_response = await api_client.get(
        f"/api/comic-builder/v2/image/{image_id}/signed-url",
        headers=headers,
    )
    assert signed_url_response.status_code == 200

    body = signed_url_response.json()
    assert "url" in body
    assert "expires_at" in body

    # expires_at is in the future
    expires_at = datetime.fromisoformat(body["expires_at"])
    assert expires_at > datetime.now(timezone.utc)

    # URL is actually accessible — GCS returns 200 for the image
    async with httpx.AsyncClient() as client:
        image_response = await client.get(body["url"])
    assert image_response.status_code == 200
    assert "image" in image_response.headers.get("content-type", "")

    if DELETE_TEST_UPLOADS_AFTER_TEST:
        _delete_gcs_prefix(user)


@pytest.mark.manual
@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_character_reference_images_via_endpoint(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """After uploading a reference image, the list endpoint returns it."""
    repo = RepositoryV2(db_session)
    service = ImageService(db=db_session, repository_v2=repo)

    # Upload one reference image directly via service
    uploaded = await service.upload_reference_image(
        user_id=str(user.id),
        project_id=project.id,
        story_id=story.id,
        character_id=character.id,
        image_byte_stream=_build_test_jpeg_stream(),
    )

    # Hit the list endpoint
    access_token = JWTTokenManager().create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {access_token}"}
    url = (
        f"/api/comic-builder/v2/project/{project.id}"
        f"/story/{story.id}"
        f"/character/{character.id}/reference-images"
    )
    response = await api_client.get(url, headers=headers)
    assert response.status_code == 200

    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1

    item = body[0]
    assert item["id"] == str(uploaded.id)
    assert item["objectKey"] == uploaded.object_key
    assert item["bucket"] == uploaded.bucket
    assert item["width"] > 0
    assert item["height"] > 0
    assert item["sizeBytes"] > 0

    if DELETE_TEST_UPLOADS_AFTER_TEST:
        _delete_gcs_prefix(user)
