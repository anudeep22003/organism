"""
Story 70 test gate — GET /panel/{panel_id}/renders endpoint.

Test invariants:
  1. GET .../renders returns 200 with all render Image rows ordered newest first.
  2. Returns an empty list when no renders exist (not 404).
  3. Returns 404 when the panel does not exist.
  4. After two renders, both are returned with the newest first.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.story_engine.models import Panel, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


async def test_list_panel_renders_returns_200_ordered_newest_first(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET /renders returns renders ordered newest first."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    first = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="test/first.jpg",
        bucket="test-bucket",
        size_bytes=100,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(first)
    await db_session.flush()

    second = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="test/second.jpg",
        bucket="test-bucket",
        size_bytes=200,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(second)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/renders",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert len(body) == 2
    # Newest first — second was created after first
    assert body[0]["id"] == str(second.id)
    assert body[1]["id"] == str(first.id)


async def test_list_panel_renders_returns_empty_list_when_no_renders(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns empty list (not 404) when panel exists but has no renders."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/renders",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_list_panel_renders_returns_404_when_panel_not_found(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 when the panel does not exist."""
    nonexistent = uuid.uuid4()
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{nonexistent}/renders",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_list_panel_renders_after_two_renders_both_returned(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """After two renders, both Image rows are returned."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    for i in range(2):
        render = ImageModel.create(
            project_id=project.id,
            user_id=user.id,
            target_id=panel.id,
            width=512,
            height=512,
            content_type=ImageContentType.JPEG,
            object_key=f"test/render-{i}.jpg",
            bucket="test-bucket",
            size_bytes=100 * (i + 1),
            discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
        )
        db_session.add(render)

    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}"
        f"/panel/{panel.id}/renders",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
