"""
Tests for POST .../character/{character_id}/set-canonical-render.

Test invariants:
  1. 200 — sets canonical render; canonicalRender in response matches the chosen image
  2. 404 — image does not exist
  3. 404 — image belongs to a different character
  4. 404 — image has the wrong discriminator (reference, not render)
  5. 404 — character does not exist
  6. 401 — no auth token
  7. get_canonical_character_render prefers canonical_render_id over most recent
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth_v2.models.user import User
from core.story_engine.models import Character, Project, Story
from core.story_engine.models.image import Image as ImageModel
from core.story_engine.models.image import ImageContentType, ImageDiscriminatorKey
from tests.auth_helpers import auth_cookie_header


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    return auth_cookie_header(user_id)


def _url(project_id: uuid.UUID, story_id: uuid.UUID, character_id: uuid.UUID) -> str:
    return (
        f"/api/comic-builder/v2/project/{project_id}"
        f"/story/{story_id}/character/{character_id}/set-canonical-render"
    )


def _make_render(
    project: Project,
    user: User,
    character: Character,
    object_key: str = "char/render-canonical.jpg",
) -> ImageModel:
    return ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key=object_key,
        bucket="test-bucket",
        size_bytes=2048,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_RENDER,
    )


async def test_set_canonical_render_200(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """200 — response canonicalRender.id matches the chosen image."""
    render = _make_render(project, user, character)
    db_session.add(render)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(render.id)},
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["canonicalRender"]["id"] == str(render.id)


async def test_set_canonical_render_404_bad_image(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image does not exist."""
    response = await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(uuid.uuid4())},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_render_404_wrong_character(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image belongs to a different character."""
    other = Character(
        story_id=story.id,
        name="Legolas",
        slug="legolas",
        attributes={"name": "Legolas"},
    )
    db_session.add(other)
    await db_session.flush()

    render = _make_render(project, user, other, object_key="char/render-other.jpg")
    db_session.add(render)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(render.id)},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_render_404_wrong_discriminator(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the image is a reference image, not a render."""
    ref = ImageModel.create(
        project_id=project.id,
        user_id=user.id,
        target_id=character.id,
        width=512,
        height=512,
        content_type=ImageContentType.JPEG,
        object_key="char/ref-disc.jpg",
        bucket="test-bucket",
        size_bytes=1024,
        discriminator_key=ImageDiscriminatorKey.CHARACTER_REFERENCE,
    )
    db_session.add(ref)
    await db_session.commit()

    response = await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(ref.id)},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_render_404_bad_character(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """404 when the character does not exist."""
    response = await api_client.post(
        _url(project.id, story.id, uuid.uuid4()),
        json={"imageId": str(uuid.uuid4())},
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_set_canonical_render_401_no_token(
    api_client: AsyncClient,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """401 when no auth token is provided."""
    response = await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(uuid.uuid4())},
    )
    assert response.status_code == 401


async def test_canonical_render_prefers_set_over_most_recent(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """After set-canonical-render, GET character returns the chosen render not the newest."""
    older_render = _make_render(
        project, user, character, object_key="char/render-older.jpg"
    )
    newer_render = _make_render(
        project, user, character, object_key="char/render-newer.jpg"
    )
    db_session.add(older_render)
    db_session.add(newer_render)
    await db_session.commit()

    # Set the older render as canonical
    await api_client.post(
        _url(project.id, story.id, character.id),
        json={"imageId": str(older_render.id)},
        headers=_auth_headers(user.id),
    )

    # GET character — canonical render should be the older one, not the newer
    get_response = await api_client.get(
        f"/api/comic-builder/v2/project/{project.id}/story/{story.id}/character/{character.id}",
    )
    assert get_response.status_code == 200
    assert get_response.json()["canonicalRender"]["id"] == str(older_render.id)
