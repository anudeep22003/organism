"""
Story 60 test gate — POST /panel/{panel_id}/render endpoint.

Test invariants:
  1. render_panel creates an Image row with target_id=panel_id and
     discriminator_key=panel_render.
  2. Creates an EditEvent(RENDER_PANEL, SUCCEEDED).
  3. output_snapshot on the EditEvent contains {"image_id": "<uuid>"}.
  4. Calling render_panel twice creates two Image rows for the same panel.
  5. get_canonical_render returns the most recently created Image.
  6. Characters with no render are skipped gracefully (no exception).
  7. Returns 404 for a panel that does not exist.
  8. EditEvent is marked FAILED when fal raises an exception.
"""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.story_engine.models import Character, Panel, Project, Story
from core.story_engine.models.edit_event import (
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from core.story_engine.models.panel_character import PanelCharacter
from core.story_engine.repository import Repository
from core.story_engine.service.image_service import StorageReceipt
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _minimal_jpeg_bytes() -> bytes:
    """Return a valid 1×1 JPEG so PIL can parse real dimensions in render paths."""
    buf = BytesIO()
    PILImage.new("RGB", (1, 1), color=(255, 0, 0)).save(buf, format="JPEG")
    return buf.getvalue()


def _mock_fal_response(url: str = "https://fal.ai/render/test-image.jpg") -> dict:
    return {"images": [{"url": url}]}


def _make_mock_httpx(fake_bytes: bytes | None = None) -> AsyncMock:
    mock_resp = MagicMock()
    mock_resp.content = fake_bytes if fake_bytes is not None else _minimal_jpeg_bytes()
    mock_resp.headers = {"content-type": "image/jpeg"}
    mock_resp.raise_for_status = MagicMock()
    mock_httpx_ctx = AsyncMock()
    mock_httpx_ctx.__aenter__ = AsyncMock(return_value=mock_httpx_ctx)
    mock_httpx_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_httpx_ctx.get = AsyncMock(return_value=mock_resp)
    return mock_httpx_ctx


async def test_render_panel_creates_image_row_with_panel_render_discriminator(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """render_panel creates Image row with target_id=panel_id, discriminator=panel_render."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/test-key",
        bucket="test-bucket",
    )

    with (
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.image_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.panel_service.httpx.AsyncClient",
            return_value=_make_mock_httpx(),
        ),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/render",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(ImageModel).where(
            ImageModel.target_id == panel.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.PANEL_RENDER,
        )
    )
    images = list(result.scalars().all())
    assert len(images) == 1
    assert images[0].target_id == panel.id
    assert images[0].discriminator_key == ImageDiscriminatorKey.PANEL_RENDER


async def test_render_panel_creates_edit_event_render_panel_succeeded(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Creates an EditEvent(RENDER_PANEL, SUCCEEDED)."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/test-key",
        bucket="test-bucket",
    )

    with (
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.image_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.panel_service.httpx.AsyncClient",
            return_value=_make_mock_httpx(),
        ),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/render",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_type == EditEventTargetType.PANEL,
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_PANEL,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.SUCCEEDED


async def test_render_panel_output_snapshot_contains_image_id(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """output_snapshot contains {"image_id": "<uuid>"}."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/test-key",
        bucket="test-bucket",
    )

    with (
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.image_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.panel_service.httpx.AsyncClient",
            return_value=_make_mock_httpx(),
        ),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/render",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    image_id = response.json()["canonicalRender"]["id"]

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_PANEL,
        )
    )
    event = result.scalar_one()
    assert event.output_snapshot is not None
    assert event.output_snapshot.get("image_id") == image_id


async def test_render_panel_twice_creates_two_image_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Two render calls create two Image rows (variation tracking)."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/test-key",
        bucket="test-bucket",
    )

    for _ in range(2):
        with (
            patch(
                "core.story_engine.service.panel_service.fal_async_client.subscribe",
                new_callable=AsyncMock,
                return_value=_mock_fal_response(),
            ),
            patch(
                "core.story_engine.service.image_service.GCSUploadService.upload",
                return_value=mock_receipt,
            ),
            patch(
                "core.story_engine.service.panel_service.httpx.AsyncClient",
                return_value=_make_mock_httpx(),
            ),
        ):
            await api_client.post(
                f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
                f"/panel/{panel.id}/render",
                headers=_auth_headers(user.id),
            )

    result = await db_session.execute(
        select(ImageModel).where(
            ImageModel.target_id == panel.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.PANEL_RENDER,
        )
    )
    images = list(result.scalars().all())
    assert len(images) == 2


async def test_render_panel_get_canonical_render_returns_most_recent(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """get_canonical_render returns the most recently created Image."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    older = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="test/older.jpg",
        bucket="test-bucket",
        size_bytes=100,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(older)
    await db_session.flush()

    newer = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="test/newer.jpg",
        bucket="test-bucket",
        size_bytes=200,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(newer)
    await db_session.commit()

    repo = Repository(db_session)
    canonical = await repo.image.get_canonical_render(
        target_id=panel.id,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    assert canonical is not None
    assert canonical.id == newer.id


async def test_render_panel_characters_without_render_skipped_gracefully(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Characters with no render are skipped gracefully (no exception)."""
    # Panel references the character, but character has no render image
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={
            "background": "Forest",
            "dialogue": "Hi",
            "characters": [character.slug],
        },
    )
    db_session.add(panel)
    await db_session.flush()

    join_row = PanelCharacter(panel_id=panel.id, character_id=character.id)
    db_session.add(join_row)
    await db_session.commit()

    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/test-key",
        bucket="test-bucket",
    )

    with (
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.image_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.panel_service.httpx.AsyncClient",
            return_value=_make_mock_httpx(),
        ),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/render",
            headers=_auth_headers(user.id),
        )

    # Should succeed even though the character has no canonical render
    assert response.status_code == 200


async def test_render_panel_returns_404_for_nonexistent_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 for a panel that does not exist."""
    nonexistent = uuid.uuid4()
    with (
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{nonexistent}/render",
            headers=_auth_headers(user.id),
        )
    assert response.status_code == 404


async def test_render_panel_edit_event_marked_failed_on_fal_error(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """EditEvent is marked FAILED when fal raises an exception."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hi", "characters": []},
    )
    db_session.add(panel)
    await db_session.commit()

    with patch(
        "core.story_engine.service.panel_service.fal_async_client.subscribe",
        new_callable=AsyncMock,
        side_effect=RuntimeError("fal unavailable"),
    ):
        response = await api_client.post(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
            f"/panel/{panel.id}/render",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 500

    result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_PANEL,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.FAILED
