"""
Tests for POST .../panel/{panel_id}/render/edit.

Test invariants (fixture-backed, no fal/GCS):
  1. Returns 401 when no Authorization header is provided.
  2. Returns 404 when the panel ID does not exist.
  3. Returns 404 when the story ID does not exist.
  4. Returns 404 when source_image_id does not exist.
  5. Returns 404 when source_image_id belongs to a different panel.

Happy-path (201 + correct ImageResponseSchema shape) requires a live fal call
and is covered by manual integration tests.
"""

import uuid

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
