"""
Story 110 test gate — DELETE /v2/project/{project_id}/story/{story_id}/panel/{panel_id}.

Test invariants:
  1. DELETE returns 204 with no body.
  2. After deletion, GET .../panel/{id} returns 404.
  3. panel_character rows for the deleted panel are gone (cascade).
  4. Image rows with target_id=panel_id and discriminator_key=panel_render are
     gone from the DB (explicit delete in service).
  5. DELETE returns 404 for a panel_id that does not exist.
  6. DELETE returns 404 when the panel belongs to a different story.
  7. DELETE requires auth.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Character, Panel, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from core.story_engine.models.panel_character import PanelCharacter

_jwt = JWTTokenManager()


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _panel_url(project_id: uuid.UUID, story_id: uuid.UUID, panel_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}/story/{story_id}/panel/{panel_id}"
    )


async def test_delete_panel_returns_204(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """DELETE an existing panel returns 204 with no body."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)

    response = await api_client.delete(
        _panel_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_panel_then_get_returns_404(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """After DELETE, GET on the same panel_id returns 404."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)

    await api_client.delete(
        _panel_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )

    get_response = await api_client.get(
        _panel_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )
    assert get_response.status_code == 404


async def test_delete_panel_cascades_panel_character_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Deleting a panel removes its panel_character join rows."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    join_row = PanelCharacter(panel_id=panel.id, character_id=character.id)
    db_session.add(join_row)
    await db_session.commit()
    await db_session.refresh(panel)

    panel_id = panel.id
    db_session.expunge_all()

    response = await api_client.delete(
        _panel_url(project.id, story.id, panel_id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 204

    result = await db_session.execute(
        text("SELECT panel_id FROM panel_character WHERE panel_id = :pid"),
        {"pid": panel_id},
    )
    assert result.fetchone() is None


async def test_delete_panel_removes_panel_render_image_rows(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Deleting a panel removes Image rows with discriminator_key=panel_render."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    image = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=panel.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="test/panel-render.jpg",
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.PANEL_RENDER,
    )
    db_session.add(image)
    await db_session.commit()
    await db_session.refresh(panel)

    panel_id = panel.id
    image_id = image.id
    db_session.expunge_all()

    response = await api_client.delete(
        _panel_url(project.id, story.id, panel_id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 204

    result = await db_session.execute(
        text("SELECT id FROM image WHERE id = :id"), {"id": image_id}
    )
    assert result.fetchone() is None


async def test_delete_panel_404_for_nonexistent_panel(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """DELETE on a panel_id that does not exist returns 404."""
    response = await api_client.delete(
        _panel_url(project.id, story.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_panel_404_for_panel_in_different_story(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """DELETE returns 404 when the panel belongs to a different story."""
    other_story = Story(project_id=project.id, story_text="Other story")
    db_session.add(other_story)
    await db_session.flush()

    panel = Panel.create(story_id=other_story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)

    # Attempt to delete the panel under the wrong story_id
    response = await api_client.delete(
        _panel_url(project.id, story.id, panel.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_panel_requires_auth(
    api_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
    story: Story,
) -> None:
    """DELETE without a token returns 401."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)

    response = await api_client.delete(_panel_url(project.id, story.id, panel.id))
    assert response.status_code == 401
