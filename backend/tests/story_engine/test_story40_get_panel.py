"""
Story 40 test gate — GET /panel/{panel_id} endpoint.

Test invariants:
  1. GET .../panel/{id} returns 200 with the correct panel.
  2. Returns 404 for a panel_id that does not exist.
  3. Returns 404 for a panel_id that exists but belongs to a different story.
  4. canonical_render is null when no render exists.
  5. canonical_render is populated with the latest image when a render exists.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Panel, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = JWTTokenManager().create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


async def test_get_panel_returns_200(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """GET /panel/{id} returns 200 with correct panel data."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "Forest", "dialogue": "Hello"},
    )
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{panel.id}",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["panel"]["id"] == str(panel.id)
    assert body["panel"]["orderIndex"] == 0
    assert body["panel"]["attributes"]["background"] == "Forest"


async def test_get_panel_returns_404_when_panel_not_found(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 for a panel_id that does not exist."""
    nonexistent = uuid.uuid4()
    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{nonexistent}",
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_get_panel_returns_404_for_panel_in_different_story(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Returns 404 for a panel_id that belongs to a different story."""
    # Create a second story
    other_story = Story(project_id=project.id, story_text="Other story")
    db_session.add(other_story)
    await db_session.flush()

    panel = Panel.create(story_id=other_story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    try:
        # Request with the wrong story_id (story instead of other_story)
        response = await api_client.get(
            f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{panel.id}",
            headers=_auth_headers(user.id),
        )
        assert response.status_code == 404
    finally:
        await db_session.delete(other_story)
        await db_session.commit()


async def test_get_panel_canonical_render_null_when_no_render(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """canonical_render is null when no render exists."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()

    response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{panel.id}",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    assert response.json()["canonicalRender"] is None  # top-level, not under panel


async def test_get_panel_canonical_render_populated_when_render_exists(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """canonical_render is populated with the latest image when a render exists."""
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
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/panel/{panel.id}",
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["canonicalRender"] is not None  # top-level, not under panel
    assert body["canonicalRender"]["id"] == str(render_image.id)
