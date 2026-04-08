"""
API tests for project and story management endpoints (v2).

GET    /api/comic-builder/v2/projects
POST   /api/comic-builder/v2/projects
GET    /api/comic-builder/v2/projects/{project_id}
POST   /api/comic-builder/v2/projects/{project_id}/story
DELETE /api/comic-builder/v2/projects/{project_id}/story/{story_id}

Invariants under test:
- Response shapes (camelCase serialisation, required fields, field types)
- DB side-effects (rows created / deleted)
- Auth boundary: 401 without a token on every endpoint
- 404 for missing resources
- Ownership isolation: a user cannot see another user's projects

No mocking. Real FastAPI app, real Postgres.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.managers.jwt import JWTTokenManager
from core.auth.models.user import User
from core.story_engine.models import Project, Story

_jwt = JWTTokenManager()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_headers(user_id: uuid.UUID) -> dict[str, str]:
    token = _jwt.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _projects_url() -> str:
    return "/api/comic-builder/v2/projects"


def _project_url(project_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/projects/{project_id}"


def _stories_url(project_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/projects/{project_id}/story"


def _story_url(project_id: uuid.UUID, story_id: uuid.UUID) -> str:
    return f"/api/comic-builder/v2/projects/{project_id}/story/{story_id}"


# ---------------------------------------------------------------------------
# GET /projects — list all projects for user
# ---------------------------------------------------------------------------


async def test_list_projects_returns_200_and_array(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """The listing endpoint returns an array containing the fixture project."""
    response = await api_client.get(_projects_url(), headers=_auth_headers(user.id))

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)

    ids = [item["id"] for item in body]
    assert str(project.id) in ids


async def test_list_projects_response_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """Each item in the list has the fields from ProjectListResponseSchema.

    Renaming or removing a field should fail this test.
    """
    response = await api_client.get(_projects_url(), headers=_auth_headers(user.id))

    assert response.status_code == 200
    item = next(i for i in response.json() if i["id"] == str(project.id))

    assert "id" in item
    assert "name" in item
    assert "createdAt" in item
    assert "updatedAt" in item
    assert "storyCount" in item
    assert isinstance(item["storyCount"], int)


async def test_list_projects_story_count_reflects_stories(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """storyCount in the list reflects the number of stories under the project."""
    response = await api_client.get(_projects_url(), headers=_auth_headers(user.id))

    item = next(i for i in response.json() if i["id"] == str(project.id))
    assert item["storyCount"] >= 1


async def test_list_projects_empty_for_new_user(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A brand new user with no projects gets an empty list."""
    unique_email = f"empty-list-{uuid.uuid4()}@example.com"
    from core.auth.models.user import User as UserModel

    new_user = UserModel(email=unique_email, password_hash="not-a-hash")
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    response = await api_client.get(_projects_url(), headers=_auth_headers(new_user.id))

    assert response.status_code == 200
    assert response.json() == []

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": new_user.id}
    )
    await db_session.commit()


async def test_list_projects_requires_auth(
    api_client: AsyncClient,
) -> None:
    """GET /projects without a token returns 401."""
    response = await api_client.get(_projects_url())
    assert response.status_code == 401


async def test_list_projects_does_not_return_other_users_projects(
    api_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
    project: Project,
) -> None:
    """A second user cannot see the first user's projects."""
    other_email = f"other-{uuid.uuid4()}@example.com"
    from core.auth.models.user import User as UserModel

    other_user = UserModel(email=other_email, password_hash="not-a-hash")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    response = await api_client.get(
        _projects_url(), headers=_auth_headers(other_user.id)
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert str(project.id) not in ids

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": other_user.id}
    )
    await db_session.commit()


# ---------------------------------------------------------------------------
# POST /projects — create a project
# ---------------------------------------------------------------------------


async def test_create_project_returns_201_and_id(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """Creating a project returns 200 with the new project's ID."""
    response = await api_client.post(
        _projects_url(),
        headers=_auth_headers(user.id),
        json={"name": "My Test Project"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    project_id = uuid.UUID(body["id"])

    # Verify the row actually exists in the DB
    result = await db_session.execute(
        text("SELECT id FROM project WHERE id = :id"), {"id": project_id}
    )
    assert result.fetchone() is not None

    # Cleanup (cascade will handle it, but we tidy up explicitly)
    await db_session.execute(
        text("DELETE FROM project WHERE id = :id"), {"id": project_id}
    )
    await db_session.commit()


async def test_create_project_persists_name(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """The name supplied at creation is stored and returned."""
    response = await api_client.post(
        _projects_url(),
        headers=_auth_headers(user.id),
        json={"name": "Named Project"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Named Project"

    await db_session.execute(
        text("DELETE FROM project WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_project_response_shape(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """The create-project response matches ProjectResponseSchema fields.

    Adding or removing fields should surface here.
    """
    response = await api_client.post(
        _projects_url(),
        headers=_auth_headers(user.id),
        json={"name": "Shape Test"},
    )

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    assert "name" in body
    assert "createdAt" in body
    assert "updatedAt" in body
    assert "state" in body  # legacy state blob — must still be present

    await db_session.execute(
        text("DELETE FROM project WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_project_without_name(
    api_client: AsyncClient,
    user: User,
    db_session: AsyncSession,
) -> None:
    """Name is optional — omitting it returns 200 and null name."""
    response = await api_client.post(
        _projects_url(),
        headers=_auth_headers(user.id),
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] is None

    await db_session.execute(
        text("DELETE FROM project WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_project_requires_auth(
    api_client: AsyncClient,
) -> None:
    """POST /projects without a token returns 401."""
    response = await api_client.post(_projects_url(), json={"name": "Unauthorized"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /projects/{project_id} — project details with stories
# ---------------------------------------------------------------------------


async def test_get_project_returns_200(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """Fetching an existing project by ID returns 200."""
    response = await api_client.get(
        _project_url(project.id), headers=_auth_headers(user.id)
    )
    assert response.status_code == 200


async def test_get_project_response_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """ProjectRelationalStateSchema includes a nested stories array.

    Removing the stories field or flattening the schema should fail here.
    """
    response = await api_client.get(
        _project_url(project.id), headers=_auth_headers(user.id)
    )

    assert response.status_code == 200
    body = response.json()

    assert body["id"] == str(project.id)
    assert "stories" in body
    assert isinstance(body["stories"], list)

    story_ids = [s["id"] for s in body["stories"]]
    assert str(story.id) in story_ids


async def test_get_project_story_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Nested story objects include the expected StoryResponseSchema fields."""
    response = await api_client.get(
        _project_url(project.id), headers=_auth_headers(user.id)
    )

    assert response.status_code == 200
    nested_story = next(
        s for s in response.json()["stories"] if s["id"] == str(story.id)
    )

    assert "id" in nested_story
    assert "projectId" in nested_story
    assert "storyText" in nested_story
    assert "userInputText" in nested_story
    assert "sourceEventId" in nested_story


async def test_get_project_404_for_unknown_id(
    api_client: AsyncClient,
    user: User,
) -> None:
    """Fetching a project that doesn't exist returns 404."""
    response = await api_client.get(
        _project_url(uuid.uuid4()), headers=_auth_headers(user.id)
    )
    assert response.status_code == 404


async def test_get_project_404_for_other_users_project(
    api_client: AsyncClient,
    db_session: AsyncSession,
    project: Project,
) -> None:
    """A different user cannot fetch another user's project by ID."""
    from core.auth.models.user import User as UserModel

    other_user = UserModel(
        email=f"isolation-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    response = await api_client.get(
        _project_url(project.id), headers=_auth_headers(other_user.id)
    )
    assert response.status_code == 404

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": other_user.id}
    )
    await db_session.commit()


async def test_get_project_requires_auth(
    api_client: AsyncClient,
    project: Project,
) -> None:
    """GET /projects/{id} without a token returns 401."""
    response = await api_client.get(_project_url(project.id))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /projects/{project_id}/story — create a story
# ---------------------------------------------------------------------------


async def test_create_story_returns_200_and_id(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """Creating a story under a project returns 200 with the new story's ID."""
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={"projectId": str(project.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    story_id = uuid.UUID(body["id"])

    # Verify the row exists in the DB
    result = await db_session.execute(
        text("SELECT id FROM story WHERE id = :id"), {"id": story_id}
    )
    assert result.fetchone() is not None

    # Cleanup (cascade from project handles it, but be explicit)
    await db_session.execute(text("DELETE FROM story WHERE id = :id"), {"id": story_id})
    await db_session.commit()


async def test_create_story_response_shape(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """The create-story response matches StoryResponseSchema.

    Changing the schema's field names or types surfaces here.
    """
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={"projectId": str(project.id)},
    )

    assert response.status_code == 200
    body = response.json()

    assert "id" in body
    assert "projectId" in body
    assert body["projectId"] == str(project.id)
    assert "storyText" in body
    assert "userInputText" in body
    assert "sourceEventId" in body
    assert body["sourceEventId"] is None  # freshly created — no event yet

    story_id = uuid.UUID(body["id"])
    await db_session.execute(text("DELETE FROM story WHERE id = :id"), {"id": story_id})
    await db_session.commit()


async def test_create_story_story_text_starts_empty(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """A newly created story has empty story_text before any generation."""
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={"projectId": str(project.id)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["storyText"] == ""

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_with_meta_generates_name_and_description(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """Sending metadata at story creation causes the LLM to populate name and description."""
    meta_payload = {
        "about": "Anton Chekhov's - In the Cart",
        "tone": "Emotional",
        "comicStyle": "Western",
        "hasBackdrop": "Yes",
        "backdrop": "1900 rural Russia village",
        "forSomeone": "Yes",
        "relationship": "friend who is interested in stories",
        "feeling": ["Moved"],
    }
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={"meta": meta_payload},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["name"] is not None
    assert isinstance(body["name"], str)
    assert 0 < len(body["name"]) <= 100

    assert body["description"] is not None
    assert isinstance(body["description"], str)
    assert 0 < len(body["description"]) <= 300

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_without_meta_has_null_name_and_description(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """A story created with no metadata has null name and description."""
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] is None
    assert body["description"] is None

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_persists_meta(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """Meta supplied at creation is stored and returned in the response."""
    meta_payload = {
        "about": "Anton Chekhov's - In the Cart",
        "tone": "Emotional",
        "comicStyle": "Western",
    }
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={"meta": meta_payload},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["meta"] == meta_payload

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_with_name_and_description_skips_llm(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """When name and description are both provided, the LLM is not called and the
    exact values sent are returned unchanged."""
    provided_name = "Echoes of the Steppe"
    provided_description = "A quiet Western set in rural Russia, gifted to a friend."
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={
            "name": provided_name,
            "description": provided_description,
            "meta": {
                "about": "Anton Chekhov's - In the Cart",
                "tone": "Emotional",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == provided_name
    assert body["description"] == provided_description

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_with_partial_identity_fills_missing_field(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """When only name is provided, the LLM fills in the missing description
    without overwriting the user-supplied name."""
    provided_name = "Echoes of the Steppe"
    response = await api_client.post(
        _stories_url(project.id),
        headers=_auth_headers(user.id),
        json={
            "name": provided_name,
            "meta": {
                "about": "Anton Chekhov's - In the Cart",
                "tone": "Emotional",
                "comicStyle": "Western",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == provided_name
    assert body["description"] is not None
    assert isinstance(body["description"], str)
    assert len(body["description"]) > 0

    await db_session.execute(
        text("DELETE FROM story WHERE id = :id"), {"id": uuid.UUID(body["id"])}
    )
    await db_session.commit()


async def test_create_story_requires_auth(
    api_client: AsyncClient,
    project: Project,
) -> None:
    """POST /projects/{id}/story without a token returns 401."""
    response = await api_client.post(
        _stories_url(project.id),
        json={"projectId": str(project.id)},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /projects/{project_id}/story/{story_id}
# ---------------------------------------------------------------------------


async def test_delete_story_returns_204(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """DELETE on an existing story returns 204 with no body."""
    response = await api_client.delete(
        _story_url(project.id, story.id),
        headers=_auth_headers(user.id),
    )

    assert response.status_code == 204
    assert response.content == b""


async def test_delete_story_removes_row_from_db(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """After DELETE the story row is gone from the DB."""
    # Create an extra story so we don't rely on the shared fixture
    from core.story_engine.models import Story as StoryModel

    extra = StoryModel(project_id=project.id, story_text="to be deleted")
    db_session.add(extra)
    await db_session.commit()
    await db_session.refresh(extra)

    response = await api_client.delete(
        _story_url(project.id, extra.id),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 204

    result = await db_session.execute(
        text("SELECT id FROM story WHERE id = :id"), {"id": extra.id}
    )
    assert result.fetchone() is None


async def test_delete_story_then_project_details_excludes_it(
    api_client: AsyncClient,
    user: User,
    project: Project,
    db_session: AsyncSession,
) -> None:
    """After deleting a story it no longer appears in GET /projects/{id}."""
    from core.story_engine.models import Story as StoryModel

    extra = StoryModel(project_id=project.id, story_text="delete-me")
    db_session.add(extra)
    await db_session.commit()
    await db_session.refresh(extra)

    await api_client.delete(
        _story_url(project.id, extra.id),
        headers=_auth_headers(user.id),
    )

    details_resp = await api_client.get(
        _project_url(project.id), headers=_auth_headers(user.id)
    )
    story_ids = [s["id"] for s in details_resp.json()["stories"]]
    assert str(extra.id) not in story_ids


async def test_delete_story_404_unknown_story(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """DELETE on a non-existent story ID returns 404."""
    response = await api_client.delete(
        _story_url(project.id, uuid.uuid4()),
        headers=_auth_headers(user.id),
    )
    assert response.status_code == 404


async def test_delete_story_requires_auth(
    api_client: AsyncClient,
    project: Project,
    story: Story,
) -> None:
    """DELETE /projects/{id}/story/{id} without a token returns 401."""
    response = await api_client.delete(_story_url(project.id, story.id))
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /projects/me — get-or-create default project
# ---------------------------------------------------------------------------


def _my_project_url() -> str:
    return "/api/comic-builder/v2/projects/me"


async def test_my_project_creates_on_first_call(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A brand new user gets a project created automatically on first call."""
    from core.auth.models.user import User as UserModel

    new_user = UserModel(
        email=f"my-project-new-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    response = await api_client.get(
        _my_project_url(), headers=_auth_headers(new_user.id)
    )

    assert response.status_code == 200
    body = response.json()
    assert "id" in body
    uuid.UUID(body["id"])  # must be a valid UUID
    assert body["stories"] == []

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": new_user.id}
    )
    await db_session.commit()


async def test_my_project_is_idempotent(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Calling /projects/me twice returns the same project ID both times."""
    from core.auth.models.user import User as UserModel

    new_user = UserModel(
        email=f"my-project-idempotent-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add(new_user)
    await db_session.commit()
    await db_session.refresh(new_user)

    first = await api_client.get(_my_project_url(), headers=_auth_headers(new_user.id))
    second = await api_client.get(_my_project_url(), headers=_auth_headers(new_user.id))

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    # Only one project row should exist for this user
    result = await db_session.execute(
        text("SELECT COUNT(*) FROM project WHERE user_id = :uid"),
        {"uid": new_user.id},
    )
    assert result.scalar() == 1

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": new_user.id}
    )
    await db_session.commit()


async def test_my_project_returns_existing_project(
    api_client: AsyncClient,
    user: User,
    project: Project,
) -> None:
    """If a project already exists, /projects/me returns that same project."""
    response = await api_client.get(_my_project_url(), headers=_auth_headers(user.id))

    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)


async def test_my_project_includes_stories(
    api_client: AsyncClient,
    user: User,
    project: Project,
    story: Story,
) -> None:
    """Stories belonging to the project are included in the response."""
    response = await api_client.get(_my_project_url(), headers=_auth_headers(user.id))

    assert response.status_code == 200
    body = response.json()
    assert "stories" in body
    story_ids = [s["id"] for s in body["stories"]]
    assert str(story.id) in story_ids


async def test_my_project_401_no_token(
    api_client: AsyncClient,
) -> None:
    """GET /projects/me without a token returns 401."""
    response = await api_client.get(_my_project_url())
    assert response.status_code == 401


async def test_my_project_user_isolation(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Two different users each get their own distinct project."""
    from core.auth.models.user import User as UserModel

    user_a = UserModel(
        email=f"isolation-a-{uuid.uuid4()}@example.com", password_hash="x"
    )
    user_b = UserModel(
        email=f"isolation-b-{uuid.uuid4()}@example.com", password_hash="x"
    )
    db_session.add_all([user_a, user_b])
    await db_session.commit()
    await db_session.refresh(user_a)
    await db_session.refresh(user_b)

    resp_a = await api_client.get(_my_project_url(), headers=_auth_headers(user_a.id))
    resp_b = await api_client.get(_my_project_url(), headers=_auth_headers(user_b.id))

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert resp_a.json()["id"] != resp_b.json()["id"]

    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": user_a.id}
    )
    await db_session.execute(
        text('DELETE FROM "user" WHERE id = :id'), {"id": user_b.id}
    )
    await db_session.commit()
