"""
Tests for POST .../panel/{panel_id}/render/edit.

Test invariants (fixture-backed, no fal/GCS):
  1. Returns 401 when no Authorization header is provided.
  2. Returns 404 when the panel ID does not exist.
  3. Returns 404 when the story ID does not exist.
  4. Returns 404 when source_image_id does not exist.
  5. Returns 404 when source_image_id belongs to a different panel.
  6. Character canonical renders are included in the fal image_urls, and
     character_render_ids appear in the edit event input_snapshot.
"""

import uuid
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient
from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Character, Panel, Project, Story
from core.story_engine.models.edit_event import EditEvent, EditEventOperationType
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from core.story_engine.models.panel_character import PanelCharacter
from core.story_engine.service.image_service import StorageReceipt

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _edit_url(
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/render/edit"
    )


def _body(source_image_id: uuid.UUID) -> dict:
    return {
        "instruction": "darken the sky",
        "sourceImageId": str(source_image_id),
    }


def _make_panel(story: Story, order_index: int = 0) -> Panel:
    return Panel.create(
        story_id=story.id,
        order_index=order_index,
        attributes={"background": "a dark forest", "dialogue": "", "characters": []},
    )


def _make_render_image(
    project: Project,
    user: User,
    panel: Panel,
    object_key: str = "panel/render-edit-src.jpg",
) -> ImageModel:
    return ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key=object_key,
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )


async def test_render_panel_edit_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """POST without auth returns 401."""
    panel = _make_panel(story)
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.post(
        _edit_url(project.id, story.id, panel.id),
        json=_body(uuid.uuid4()),
    )
    assert response.status_code == 401


async def test_render_panel_edit_404_bad_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """POST with a nonexistent panel ID returns 404."""
    response = await api_client.post(
        _edit_url(project.id, story.id, uuid.uuid4()),
        json=_body(uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_render_panel_edit_404_bad_story(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """POST with a nonexistent story ID returns 404."""
    panel = _make_panel(story)
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.post(
        _edit_url(project.id, uuid.uuid4(), panel.id),
        json=_body(uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_render_panel_edit_404_bad_source_image(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    db_session: AsyncSession,
) -> None:
    """POST with a nonexistent source_image_id returns 404."""
    panel = _make_panel(story)
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.post(
        _edit_url(project.id, story.id, panel.id),
        json=_body(uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_render_panel_edit_404_source_image_wrong_panel(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """POST with a source image belonging to a different panel returns 404."""
    panel_a = _make_panel(story, order_index=0)
    panel_b = _make_panel(story, order_index=1)
    db_session.add(panel_a)
    db_session.add(panel_b)
    await db_session.flush()

    image = _make_render_image(project, user, panel_a, object_key="panel/render-a.jpg")
    db_session.add(image)
    await db_session.commit()

    # Try to use panel_a's image as source for panel_b
    response = await api_client.post(
        _edit_url(project.id, story.id, panel_b.id),
        json=_body(image.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_render_panel_edit_includes_character_renders_in_fal_call(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Character canonical renders are passed to fal and recorded in input_snapshot."""
    panel = _make_panel(story)
    db_session.add(panel)
    await db_session.flush()

    # Assign the character to the panel via the join table
    db_session.add(PanelCharacter(panel_id=panel.id, character_id=character.id))

    # Source panel render image
    source_image = _make_render_image(project, user, panel, object_key="panel/src.jpg")
    db_session.add(source_image)

    # Character canonical render image
    character_render = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="character/render.jpg",
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(character_render)
    await db_session.commit()

    # Build a minimal valid JPEG for the fal response download
    buf = BytesIO()
    PILImage.new("RGB", (1, 1), color=(0, 0, 0)).save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    mock_fal_response = {"images": [{"url": "https://fal.ai/result.jpg"}]}
    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/panel/{panel.id}/renders/edit-key",
        bucket="test-bucket",
    )

    mock_httpx_resp = MagicMock()
    mock_httpx_resp.content = jpeg_bytes
    mock_httpx_resp.headers = {"content-type": "image/jpeg"}
    mock_httpx_resp.raise_for_status = MagicMock()
    mock_httpx_ctx = AsyncMock()
    mock_httpx_ctx.__aenter__ = AsyncMock(return_value=mock_httpx_ctx)
    mock_httpx_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_httpx_ctx.get = AsyncMock(return_value=mock_httpx_resp)

    captured_fal_args: dict = {}

    async def _capture_fal(**kwargs: object) -> dict:
        captured_fal_args.update(kwargs)
        return mock_fal_response

    # GCSUploadService is accessed via get_gcs_upload_service() — mock the
    # returned instance so generate_signed_url and upload are both controlled.
    mock_gcs = MagicMock()
    mock_gcs.generate_signed_url.side_effect = lambda object_key: (
        f"https://signed/{object_key}",
        None,
    )
    mock_gcs.upload.return_value = mock_receipt

    with (
        patch(
            "core.story_engine.service.panel_service.get_gcs_upload_service",
            return_value=mock_gcs,
        ),
        patch(
            "core.story_engine.service.panel_service.fal_async_client.subscribe",
            side_effect=_capture_fal,
        ),
        patch(
            "core.story_engine.service.panel_service.httpx.AsyncClient",
            return_value=mock_httpx_ctx,
        ),
    ):
        response = await api_client.post(
            _edit_url(project.id, story.id, panel.id),
            json=_body(source_image.id),
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 201

    # fal received both the source image URL and the character render URL
    fal_image_urls: list[str] = captured_fal_args.get("arguments", {}).get(
        "image_urls", []
    )
    assert len(fal_image_urls) == 2
    assert "https://signed/panel/src.jpg" in fal_image_urls
    assert "https://signed/character/render.jpg" in fal_image_urls

    # input_snapshot records character_render_ids
    event_result = await db_session.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_PANEL_EDIT,
        )
    )
    event = event_result.scalar_one()
    assert event.input_snapshot is not None
    assert str(character_render.id) in event.input_snapshot["character_render_ids"]
