"""
Tests for panel reference image endpoints.

Covers:
  upload-reference-image:
    1. 201 — creates Image row with target_id=panel_id, discriminator=PANEL_REFERENCE,
       UPLOAD_REFERENCE_IMAGE edit event with output_snapshot
    2. response referenceImages list contains the uploaded image
    3. 404 — panel does not exist
    4. 401 — no auth token

  reference-images (list):
    5. returns uploaded reference images
    6. returns empty list when none exist

  delete-reference-image:
    7. 204 — success; subsequent list returns empty
    8. 404 — image does not exist
    9. 404 — image belongs to a different panel (cross-panel guard)
    10. 404 — wrong discriminator (PANEL_RENDER passed instead of PANEL_REFERENCE)
    11. 401 — no auth token
"""

import io
import uuid
from io import BytesIO
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import EditEvent, Panel, Project, Story
from core.story_engine.models.edit_event import EditEventOperationType, EditEventStatus
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from core.story_engine.service.image_service import StorageReceipt
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _upload_url(project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/upload-reference-image"
    )


def _list_url(project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/reference-images"
    )


def _delete_url(
    project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID, image_id: uuid.UUID
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/reference-image/{image_id}"
    )


def _make_minimal_jpeg() -> io.BytesIO:
    """Return a tiny valid JPEG byte stream for upload tests."""
    from PIL import Image as PILImage

    buf = BytesIO()
    PILImage.new("RGB", (10, 10), color=(0, 128, 255)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _mock_receipt(panel_id: uuid.UUID, user_id: uuid.UUID) -> StorageReceipt:
    return StorageReceipt(
        object_key=f"{user_id}/panel/{panel_id}/references/test-key",
        bucket="test-bucket",
    )


# ---------------------------------------------------------------------------
# upload-reference-image tests
# ---------------------------------------------------------------------------


async def test_upload_panel_reference_image_201(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """201 — creates PANEL_REFERENCE Image row with correct target_id and edit event."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    receipt = _mock_receipt(panel.id, user.id)

    with patch(
        "core.story_engine.service.image_service.GCSUploadService.upload",
        return_value=receipt,
    ):
        response = await api_client.post(
            _upload_url(project.id, story.id, panel.id),
            files={"image": ("ref.jpg", _make_minimal_jpeg(), "image/jpeg")},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    body = response.json()
    assert len(body["referenceImages"]) == 1
    ref_image = body["referenceImages"][0]
    assert ref_image["bucket"] == "test-bucket"

    # Verify DB state
    result = await db_session.execute(
        select(ImageModel).where(
            ImageModel.target_id == panel.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.PANEL_REFERENCE,
        )
    )
    image_row = result.scalar_one_or_none()
    assert image_row is not None
    assert image_row.user_id == user.id
    assert image_row.project_id == project.id


async def test_upload_panel_reference_image_creates_edit_event(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """UPLOAD_REFERENCE_IMAGE edit event is created with SUCCEEDED status and output_snapshot."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    receipt = _mock_receipt(panel.id, user.id)

    with patch(
        "core.story_engine.service.image_service.GCSUploadService.upload",
        return_value=receipt,
    ):
        response = await api_client.post(
            _upload_url(project.id, story.id, panel.id),
            files={"image": ("ref.jpg", _make_minimal_jpeg(), "image/jpeg")},
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201
    image_id = response.json()["referenceImages"][0]["id"]

    event_result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.UPLOAD_REFERENCE_IMAGE,
        )
    )
    event = event_result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.SUCCEEDED
    assert event.output_snapshot is not None
    assert event.output_snapshot["image_id"] == image_id


async def test_upload_panel_reference_image_404_bad_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the panel does not exist."""
    with patch(
        "core.story_engine.service.image_service.GCSUploadService.upload",
    ):
        response = await api_client.post(
            _upload_url(project.id, story.id, uuid.uuid4()),
            files={"image": ("ref.jpg", _make_minimal_jpeg(), "image/jpeg")},
            headers=_auth_headers(user.id),
        )
    assert response.status_code == 404


async def test_upload_panel_reference_image_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 when no auth token is provided."""
    response = await api_client.post(
        _upload_url(project.id, story.id, uuid.uuid4()),
        files={"image": ("ref.jpg", _make_minimal_jpeg(), "image/jpeg")},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# reference-images (list) tests
# ---------------------------------------------------------------------------


async def test_list_panel_reference_images_returns_uploaded(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET reference-images returns the uploaded reference image."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    ref_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=10,
        height=10,
        content_type=ImageContentType.JPEG,
        object_key="panel/ref-list.jpg",
        bucket="test-bucket",
        size_bytes=512,
        discriminator_key=ImageDiscriminatorKey.PANEL_REFERENCE,
    )
    db_session.add(ref_image)
    await db_session.commit()

    response = await api_client.get(
        _list_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["id"] == str(ref_image.id)


async def test_list_panel_reference_images_empty(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET reference-images returns empty list when none exist."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        _list_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# delete-reference-image tests
# ---------------------------------------------------------------------------


async def test_delete_panel_reference_image_204(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """204 success — image is deleted; subsequent list returns empty."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    ref_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=10,
        height=10,
        content_type=ImageContentType.JPEG,
        object_key="panel/ref-delete.jpg",
        bucket="test-bucket",
        size_bytes=512,
        discriminator_key=ImageDiscriminatorKey.PANEL_REFERENCE,
    )
    db_session.add(ref_image)
    await db_session.commit()

    delete_response = await api_client.delete(
        _delete_url(project.id, story.id, panel.id, ref_image.id),
        headers=_auth_headers(user.id),
    )
    assert delete_response.status_code == 204

    list_response = await api_client.get(
        _list_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )
    assert list_response.json() == []


async def test_delete_panel_reference_image_404_bad_image(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the image does not exist."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, panel.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_panel_reference_image_404_wrong_panel(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the image belongs to a different panel (cross-panel guard)."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    other_panel = Panel.create(story_id=story.id, order_index=1, attributes={})
    db_session.add_all([panel, other_panel])
    await db_session.flush()

    ref_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=other_panel.id,  # belongs to other_panel
        width=10,
        height=10,
        content_type=ImageContentType.JPEG,
        object_key="panel/ref-wrong-panel.jpg",
        bucket="test-bucket",
        size_bytes=512,
        discriminator_key=ImageDiscriminatorKey.PANEL_REFERENCE,
    )
    db_session.add(ref_image)
    await db_session.commit()

    # Try to delete against panel (not other_panel)
    response = await api_client.delete(
        _delete_url(project.id, story.id, panel.id, ref_image.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_panel_reference_image_404_wrong_discriminator(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the image is a PANEL_RENDER, not a PANEL_REFERENCE."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    render_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="panel/render-not-ref.jpg",
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,  # wrong discriminator
    )
    db_session.add(render_image)
    await db_session.commit()

    response = await api_client.delete(
        _delete_url(project.id, story.id, panel.id, render_image.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_panel_reference_image_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 when no auth token is provided."""
    response = await api_client.delete(
        _delete_url(project.id, story.id, uuid.uuid4(), uuid.uuid4()),
    )
    assert response.status_code == 401
