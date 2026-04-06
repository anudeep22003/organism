"""
Tests for POST .../panel/{panel_id}/set-canonical-render.

Test invariants:
  1. 200 — sets canonical render; canonicalRender in response matches the chosen image
  2. 404 — image does not exist
  3. 404 — image belongs to a different panel
  4. 404 — image has the wrong discriminator (not a PANEL_RENDER)
  5. 404 — panel does not exist
  6. 401 — no auth token
  7. get_canonical_panel_render prefers canonical_render_id over most recent
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


def _url(project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/panel/{panel_id}/set-canonical-render"
    )


def _make_panel_render(
    project: Project,
    user: User,
    panel: Panel,
    object_key: str = "panel/render-canonical.jpg",
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


async def test_set_canonical_panel_render_200(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """200 — response canonicalRender.id matches the chosen image."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    render = _make_panel_render(project, user, panel)
    db_session.add(render)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"imageId": str(render.id)},
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["canonicalRender"]["id"] == str(render.id)


async def test_set_canonical_panel_render_404_bad_image(
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

    response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"imageId": str(uuid.uuid4())},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_panel_render_404_wrong_panel(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the image belongs to a different panel."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    other_panel = Panel.create(story_id=story.id, order_index=1, attributes={})
    db_session.add_all([panel, other_panel])
    await db_session.flush()

    # Render belongs to other_panel, but we post against panel
    render = _make_panel_render(
        project, user, other_panel, object_key="panel/render-other.jpg"
    )
    db_session.add(render)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"imageId": str(render.id)},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_panel_render_404_wrong_discriminator(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the image exists but is not a PANEL_RENDER (wrong discriminator)."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    # A CHARACTER_RENDER image — wrong discriminator for a panel
    wrong_disc_image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="panel/render-wrong-disc.jpg",
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )
    db_session.add(wrong_disc_image)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"imageId": str(wrong_disc_image.id)},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_panel_render_404_bad_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """404 when the panel does not exist."""
    response = await api_client.post(
        _url(project.id, story.id, uuid.uuid4()),
        json={"imageId": str(uuid.uuid4())},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_panel_render_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """401 when no auth token is provided."""
    response = await api_client.post(
        _url(project.id, story.id, uuid.uuid4()),
        json={"imageId": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_canonical_panel_render_prefers_set_over_most_recent(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """After set-canonical-render, GET panel returns the chosen render not the newest."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    older_render = _make_panel_render(
        project, user, panel, object_key="panel/render-older.jpg"
    )
    newer_render = _make_panel_render(
        project, user, panel, object_key="panel/render-newer.jpg"
    )
    db_session.add(older_render)
    db_session.add(newer_render)
    await db_session.commit()

    # Explicitly set the older render as canonical
    set_response = await api_client.post(
        _url(project.id, story.id, panel.id),
        json={"imageId": str(older_render.id)},
        headers=_auth_headers(user.id),
    )
    assert set_response.status_code == 200

    # GET panel — canonical render should be the older one, not the newer
    get_response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{panel.id}",
        headers=_auth_headers(user.id),
    )
    assert get_response.status_code == 200
    assert get_response.json()["canonicalRender"]["id"] == str(older_render.id)
