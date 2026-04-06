"""
Tests for the comic export endpoints.

Layer 1:
  test_export_zip_200_correct_files
  test_export_zip_422_missing_render
  test_export_zip_404_bad_story
  test_export_zip_401_no_token
"""

import io
import uuid
import zipfile
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Panel, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _minimal_jpeg_bytes() -> bytes:
    """Return a minimal valid JPEG (1×1 pixel) as bytes."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", (1, 1), (128, 64, 32)).save(buf, format="JPEG")
    return buf.getvalue()


def _make_panel_render(
    project: Project,
    user: User,
    panel: Panel,
    object_key: str = "panels/render.jpg",
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


# ---------------------------------------------------------------------------
# Layer 1 — ZIP export
# ---------------------------------------------------------------------------


async def test_export_zip_200_correct_files(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """200 — valid ZIP with correct number of files, zero-padded and ordered."""
    # Create 3 panels with canonical renders
    panels = []
    images = []
    for idx in range(3):
        panel = Panel.create(
            story_id=story.id,
            order_index=idx,
            attributes={"dialogue": f"Panel {idx} text"},
        )
        db_session.add(panel)
        await db_session.flush()

        img = _make_panel_render(
            project, user, panel, object_key=f"panels/render_{idx}.jpg"
        )
        db_session.add(img)
        await db_session.flush()

        # Set canonical render
        panel.canonical_render_id = img.id
        panels.append(panel)
        images.append(img)

    await db_session.commit()

    jpeg = _minimal_jpeg_bytes()
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/zip",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    # Verify the ZIP contents
    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = sorted(zf.namelist())
    assert len(names) == 3
    # With 3 panels, pad width = 1
    assert names[0] == "1_panel.jpg"
    assert names[1] == "2_panel.jpg"
    assert names[2] == "3_panel.jpg"
    # Each file contains valid JPEG bytes
    for name in names:
        assert zf.read(name) == jpeg


async def test_export_zip_422_missing_render(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """422 — response detail mentions missing panel positions."""
    # Panel with no canonical render
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={},
    )
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/zip",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "0" in detail  # position 0 is listed


async def test_export_zip_404_bad_story(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """404 — non-existent story returns 404."""
    nonexistent_story = uuid.uuid4()
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{nonexistent_story}/export/zip",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_export_zip_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 — no auth token returns 401."""
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/zip",
    )
    assert response.status_code == 401
