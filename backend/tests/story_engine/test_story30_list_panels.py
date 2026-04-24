"""
Story 30 test gate — GET /panels endpoint.

Test invariants:
  1. GET .../panels returns 200 with panels ordered by order_index ascending.
  2. Returns an empty list (not 404) when story exists but has no panels.
  3. Returns 404 when story does not exist.
  4. canonical_render is null for panels with no render.
  5. canonical_render is populated with the latest Image for panels that
     have been rendered.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import Panel, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


async def test_list_panels_returns_200_ordered_by_order_index(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET /panels returns 200 with panels in order_index ascending order."""
    # Create panels in reverse order to verify sorting
    panel1 = Panel.create(
        story_id=story.id, order_index=1, attributes={"background": "B"}
    )
    panel0 = Panel.create(
        story_id=story.id, order_index=0, attributes={"background": "A"}
    )
    db_session.add_all([panel1, panel0])
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["panel"]["orderIndex"] == 0
    assert body[1]["panel"]["orderIndex"] == 1


async def test_list_panels_returns_empty_list_when_no_panels(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns empty list (not 404) when story exists but has no panels."""
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 200
    assert response.json() == []


async def test_list_panels_returns_404_when_story_not_found(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """Returns 404 when the story does not exist."""
    nonexistent = uuid.uuid4()
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{nonexistent}/panels",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_list_panels_canonical_render_is_null_when_no_render(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """canonical_render is null for panels that have not been rendered."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["canonicalRender"] is None  # top-level, not under panel


async def test_list_panels_canonical_render_populated_when_render_exists(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """canonical_render is populated with the latest Image when a render exists."""
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
        object_key="test/renders/panel.jpg",
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(render_image)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panels",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["canonicalRender"] is not None  # top-level, not under panel
    assert body[0]["canonicalRender"]["id"] == str(render_image.id)
