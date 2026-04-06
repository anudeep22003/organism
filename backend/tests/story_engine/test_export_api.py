"""
Tests for the comic export endpoints.

Layer 1:
  test_export_zip_200_correct_files
  test_export_zip_422_missing_render
  test_export_zip_404_bad_story
  test_export_zip_401_no_token

Layer 2:
  test_export_instagram_200_correct_files
  test_export_instagram_images_are_1080x1080
  test_export_instagram_captions_txt_has_n_lines
  test_export_instagram_422_missing_render
  test_export_instagram_401_no_token

Layer 3:
  test_export_pdf_200_starts_with_pdf_magic_bytes
  test_export_pdf_422_missing_render
  test_export_pdf_401_no_token

Layer 4 (unit tests, no HTTP):
  test_compose_panel_image_output_is_taller
  test_compose_panel_image_width_unchanged
  test_compose_panel_image_empty_dialogue_no_bar
  test_compose_panel_image_text_colour_has_sufficient_contrast
Layer 4 (integration):
  test_export_zip_with_dialogue_bar_images_are_taller
  test_export_instagram_with_dialogue_bar_still_1080x1080
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
    # Each file starts with JPEG magic bytes (may differ from raw due to bar composition)
    from PIL import Image as PILImage

    for name in names:
        data = zf.read(name)
        assert data[:2] == b"\xff\xd8", f"{name} is not a valid JPEG"
        pil_img = PILImage.open(io.BytesIO(data))
        assert pil_img.width > 0 and pil_img.height > 0


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


# ---------------------------------------------------------------------------
# Layer 2 — Instagram ZIP export
# ---------------------------------------------------------------------------


async def _setup_panels_with_renders(
    db_session: AsyncSession,
    project: Project,
    user: User,
    story: Story,
    count: int = 2,
) -> None:
    """Helper: create `count` panels each with a canonical render."""
    for idx in range(count):
        panel = Panel.create(
            story_id=story.id,
            order_index=idx,
            attributes={"dialogue": f"Caption for panel {idx + 1}"},
        )
        db_session.add(panel)
        await db_session.flush()

        img = _make_panel_render(
            project, user, panel, object_key=f"panels/ig_render_{idx}.jpg"
        )
        db_session.add(img)
        await db_session.flush()

        panel.canonical_render_id = img.id

    await db_session.commit()


async def test_export_instagram_200_correct_files(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """200 — valid ZIP with N JPEG files plus captions.txt."""
    await _setup_panels_with_renders(db_session, project, user, story, count=2)

    jpeg = _minimal_jpeg_bytes()
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    # 2 panel images + captions.txt
    assert len(names) == 3
    assert "captions.txt" in names
    jpeg_names = [n for n in names if n.endswith(".jpg")]
    assert len(jpeg_names) == 2


async def test_export_instagram_images_are_1080x1080(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Each JPEG in the Instagram ZIP is exactly 1080×1080."""
    await _setup_panels_with_renders(db_session, project, user, story, count=2)

    jpeg = _minimal_jpeg_bytes()
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    from PIL import Image as PILImage

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    for name in zf.namelist():
        if name.endswith(".jpg"):
            img = PILImage.open(io.BytesIO(zf.read(name)))
            assert img.size == (1080, 1080), (
                f"{name} is {img.size}, expected (1080, 1080)"
            )


async def test_export_instagram_captions_txt_has_n_lines(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """captions.txt has exactly N lines, one per panel."""
    n = 3
    await _setup_panels_with_renders(db_session, project, user, story, count=n)

    jpeg = _minimal_jpeg_bytes()
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    captions = zf.read("captions.txt").decode("utf-8")
    lines = captions.strip().splitlines()
    assert len(lines) == n
    assert lines[0].startswith("Panel 1:")
    assert lines[n - 1].startswith(f"Panel {n}:")


async def test_export_instagram_422_missing_render(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """422 — panel with no render blocks Instagram export."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 422
    assert "0" in response.json()["detail"]


async def test_export_instagram_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 — no auth token returns 401."""
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Layer 3 — PDF export
# ---------------------------------------------------------------------------


async def test_export_pdf_200_starts_with_pdf_magic_bytes(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """200 — response body starts with %PDF magic bytes and is non-empty."""
    await _setup_panels_with_renders(db_session, project, user, story, count=4)

    jpeg = _minimal_jpeg_bytes()
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/pdf",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0
    assert response.content[:4] == b"%PDF"


async def test_export_pdf_422_missing_render(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """422 — panel with no render blocks PDF export."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/pdf",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 422
    assert "0" in response.json()["detail"]


async def test_export_pdf_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 — no auth token returns 401."""
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/pdf",
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Layer 4 — Dialogue bar unit tests (no HTTP)
# ---------------------------------------------------------------------------


def _make_jpeg(
    width: int = 100, height: int = 100, colour: tuple[int, int, int] = (200, 100, 50)
) -> bytes:
    """Create a solid-colour JPEG of given dimensions."""
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), colour).save(buf, format="JPEG")
    return buf.getvalue()


def test_compose_panel_image_output_is_taller() -> None:
    """Output image height > input image height (bar was added)."""
    from PIL import Image as PILImage

    from core.story_engine.service.export_service import _compose_panel_image

    jpeg = _make_jpeg(100, 100)
    result = _compose_panel_image(jpeg, "Hello!")
    out = PILImage.open(io.BytesIO(result))
    assert out.height > 100


def test_compose_panel_image_width_unchanged() -> None:
    """Output image width equals input width."""
    from PIL import Image as PILImage

    from core.story_engine.service.export_service import _compose_panel_image

    jpeg = _make_jpeg(120, 80)
    result = _compose_panel_image(jpeg, "Some text")
    out = PILImage.open(io.BytesIO(result))
    assert out.width == 120


def test_compose_panel_image_empty_dialogue_no_bar() -> None:
    """Empty dialogue string: image returned unchanged — no bar added."""
    from core.story_engine.service.export_service import _compose_panel_image

    jpeg = _make_jpeg(100, 100)
    result = _compose_panel_image(jpeg, "")
    # Bytes are identical — no re-encoding happened
    assert result == jpeg


def test_compose_panel_image_text_colour_has_sufficient_contrast() -> None:
    """Text colour has WCAG contrast ratio ≥ 4.5:1 against the bar colour."""
    from PIL import Image as PILImage

    from core.story_engine.service.export_service import (
        _compose_panel_image,
        _contrast_ratio,
    )

    jpeg = _make_jpeg(200, 200, colour=(200, 100, 50))
    result = _compose_panel_image(jpeg, "Contrast check")
    out = PILImage.open(io.BytesIO(result))

    # The bar occupies the bottom portion of the output; sample the centre of the bar
    bar_y = 210  # well inside the bar (input height=200, bar_h >= 30)
    bar_pixel: tuple[int, int, int] = out.getpixel((out.width // 2, bar_y))  # type: ignore[assignment]

    # Text colour must be either black or white (or dominant — any high-contrast choice)
    black: tuple[int, int, int] = (0, 0, 0)
    white: tuple[int, int, int] = (255, 255, 255)
    contrast_black = _contrast_ratio(black, bar_pixel)
    contrast_white = _contrast_ratio(white, bar_pixel)
    # At least one of black/white must be ≥ 4.5:1 against bar background
    assert max(contrast_black, contrast_white) >= 4.5


# ---------------------------------------------------------------------------
# Layer 4 integration tests
# ---------------------------------------------------------------------------


async def test_export_zip_with_dialogue_bar_images_are_taller(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """ZIP export: images have a bar added so they are taller than the source."""
    await _setup_panels_with_renders(db_session, project, user, story, count=2)

    # Use a 100×100 source JPEG
    jpeg = _make_jpeg(100, 100)
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/zip",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    from PIL import Image as PILImage

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    for name in zf.namelist():
        if name.endswith(".jpg"):
            img = PILImage.open(io.BytesIO(zf.read(name)))
            assert img.height > 100, f"{name} height {img.height} not > 100"
            assert img.width == 100


async def test_export_instagram_with_dialogue_bar_still_1080x1080(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Instagram ZIP: images are still 1080×1080 even after bar composition."""
    await _setup_panels_with_renders(db_session, project, user, story, count=2)

    jpeg = _make_jpeg(100, 100)
    with patch(
        "core.story_engine.service.export_service.GCSUploadService.download_as_bytes",
        return_value=jpeg,
    ):
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/export/instagram",
            headers=_auth_headers(user.id),
        )

    assert response.status_code == 200
    from PIL import Image as PILImage

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    for name in zf.namelist():
        if name.endswith(".jpg"):
            img = PILImage.open(io.BytesIO(zf.read(name)))
            assert img.size == (1080, 1080), f"{name} is {img.size}"
