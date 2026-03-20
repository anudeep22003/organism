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
from types import SimpleNamespace

import pytest
from PIL import Image

from core.story_engine.service.dto_types import UploadReferenceImageDTO
from core.story_engine.service.image_upload import ImageUploadService, ImageVariantKey

# Manual config values - replace with real IDs before running.
USER_ID = "2c2af68f-9315-4bab-8aa3-3b1a581dca8e"
PROJECT_ID = uuid.UUID("9c10291d-4b0a-4c2f-8deb-417d36a12d7b")
STORY_ID = uuid.UUID("0a358afa-670c-4729-b1d3-838a76320993")
CHARACTER_ID = uuid.UUID("61c317cf-06c9-4d95-bd06-6d9518a4eeba")
CHARACTER_SLUG = "the-sprite"
FILENAME_PREFIX = "integration-upload"


QUALITY = 95
SIDE = 2600

DELETE_TEST_UPLOADS_AFTER_TEST = True


def _build_test_jpeg_stream() -> BytesIO:
    img = Image.frombytes("RGB", (SIDE, SIDE), os.urandom(SIDE * SIDE * 3))
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=QUALITY, optimize=True)
    buffer.seek(0)
    return buffer


class StubRepository:
    async def get_character_for_user_in_project_and_story(
        self,
        user_id: str,
        project_id: uuid.UUID,
        story_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> SimpleNamespace:
        return SimpleNamespace(slug=CHARACTER_SLUG)

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


def _build_candidate_keys(
    object_key_prefix: str, variant_key: ImageVariantKey
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
    service = ImageUploadService(repository=StubRepository())  # type: ignore[arg-type]
    filename = f"{FILENAME_PREFIX}-{int(time.time())}"
    dto = UploadReferenceImageDTO(
        user_id=USER_ID,
        project_id=PROJECT_ID,
        story_id=STORY_ID,
        character_id=CHARACTER_ID,
        image=_build_test_jpeg_stream(),
        filename=filename,
    )
    object_key_prefix = (
        f"{dto.user_id}/character/{CHARACTER_SLUG}/references/{dto.filename}"
    )

    uploaded_keys: list[str] = []
    try:
        await service.upload_image(dto)

        for variant_key in (
            ImageVariantKey.ORIGINAL,
            ImageVariantKey.THUMB,
            ImageVariantKey.PREVIEW,
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
