"""
Live integration tests for the full panel pipeline against a real story.

Story:    e446a444-2480-4e38-9560-3aa90d806494
Project:  9c10291d-4b0a-4c2f-8deb-417d36a12d7b
User:     2c2af68f-9315-4bab-8aa3-3b1a581dca8e (v2@sy.com)

These tests hit the actual FastAPI app (via ASGITransport, no server needed)
and call live external services — OpenAI/instructor for extraction, fal + GCS
for rendering. NO mocks. NO teardown — rows stay in the DB so you can inspect
them after the run.

Run with:
    uv run pytest tests/story_engine/test_pipeline_integration.py -v -s -m manual

Pipeline order:
    1. Extract characters  (POST .../characters)
    2. Render character    (POST .../character/{id}/render)
    3. Extract panels      (POST .../panels/generate)
    4. Render panel        (POST .../panel/{id}/render)
"""

import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env.local before importing anything that reads settings
load_dotenv(
    dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env.local"),
    override=True,
)

from core.config import settings  # noqa: E402
from core.story_engine.models import Character, Panel  # noqa: E402
from core.story_engine.models.edit_event import (  # noqa: E402
    EditEvent,
    EditEventOperationType,
    EditEventStatus,
    EditEventTargetType,
)
from core.story_engine.models.image import Image as ImageModel  # noqa: E402
from core.story_engine.models.image import ImageDiscriminatorKey  # noqa: E402
from core.story_engine.models.panel_character import PanelCharacter  # noqa: E402
from main import fastapi_app  # noqa: E402
from tests.auth_helpers import auth_cookie_header  # noqa: E402

# ---------------------------------------------------------------------------
# Stable IDs — the real rows we are running the pipeline against
# ---------------------------------------------------------------------------

STORY_ID = uuid.UUID("e446a444-2480-4e38-9560-3aa90d806494")
PROJECT_ID = uuid.UUID("9c10291d-4b0a-4c2f-8deb-417d36a12d7b")
USER_ID = uuid.UUID("2c2af68f-9315-4bab-8aa3-3b1a581dca8e")

BASE = f"/api/comic-builder/v2/project/{PROJECT_ID}/story/{STORY_ID}"

# ---------------------------------------------------------------------------
# Shared fixtures for this module
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """A real AsyncSession for the local Postgres instance."""
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """httpx AsyncClient wired directly to the FastAPI app (no network socket)."""
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app),
        base_url="http://test",
    ) as c:
        yield c


def _auth_headers() -> dict[str, str]:
    return auth_cookie_header(USER_ID)


# ---------------------------------------------------------------------------
# Test 1 — Extract characters
# ---------------------------------------------------------------------------


@pytest.mark.manual
async def test_integration_extract_characters(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """
    POST /characters — extract characters from the live story via OpenAI/instructor.

    Idempotent: if characters already exist we skip the POST and log them.

    DB asserts after extraction:
      - At least 1 character row with story_id == STORY_ID
      - Each character has a non-empty slug and attributes dict
    """
    headers = _auth_headers()

    # --- Check existing characters -------------------------------------------
    existing_result = await db.execute(
        select(Character).where(Character.story_id == STORY_ID)
    )
    existing = list(existing_result.scalars().all())

    if existing:
        print(
            f"\n[extract_characters] {len(existing)} character(s) already exist — skipping POST"
        )
        for c in existing:
            print(f"  • {c.name} (id={c.id}, slug={c.slug})")
    else:
        print(
            "\n[extract_characters] No characters found — calling POST .../characters"
        )

        response = await client.post(f"{BASE}/characters", headers=headers)

        print(f"[extract_characters] HTTP {response.status_code}")
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )

        body = response.json()
        assert isinstance(body, list), "Response body should be a list"
        assert len(body) >= 1, "Expected at least 1 character to be extracted"

        print(f"[extract_characters] Extracted {len(body)} character(s):")
        for ch in body:
            print(f"  • {ch['name']} (id={ch['id']}, slug={ch['slug']})")

    # --- DB assertions -------------------------------------------------------
    await db.execute(text("SELECT 1"))  # keep session alive after any expiry

    db_result = await db.execute(
        select(Character).where(Character.story_id == STORY_ID)
    )
    db_characters = list(db_result.scalars().all())

    assert len(db_characters) >= 1, "Expected at least 1 character row in DB"

    for char in db_characters:
        assert char.story_id == STORY_ID, f"Character {char.id} has wrong story_id"
        assert char.slug, f"Character {char.id} has empty slug"
        assert isinstance(char.attributes, dict), (
            f"Character {char.id} attributes is not a dict"
        )
        assert char.name, f"Character {char.id} has no name"

    print(
        f"\n[extract_characters] DB verified: {len(db_characters)} character row(s) confirmed"
    )
    for char in db_characters:
        print(f"  DB • id={char.id}  name={char.name!r}  slug={char.slug!r}")
        print(f"       attributes keys: {list(char.attributes.keys())}")


# ---------------------------------------------------------------------------
# Test 2 — Render character
# ---------------------------------------------------------------------------


@pytest.mark.manual
async def test_integration_render_character(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """
    POST /character/{id}/render — render the first character via fal + GCS.

    Uses the first character found in the DB for this story.

    DB asserts after rendering:
      - An image row with target_id == character_id, discriminator_key == character_render
      - An edit_event row with operation_type == render_character, status == succeeded
      - output_snapshot contains {"image_id": "<uuid>"}
    """
    headers = _auth_headers()

    # Fetch characters from DB
    char_result = await db.execute(
        select(Character).where(Character.story_id == STORY_ID)
    )
    characters = list(char_result.scalars().all())
    assert len(characters) >= 1, (
        "No characters found in DB — run test_integration_extract_characters first"
    )

    character = characters[0]
    print(
        f"\n[render_character] Using character: {character.name!r} (id={character.id})"
    )

    # --- Check for existing render -------------------------------------------
    existing_img_result = await db.execute(
        select(ImageModel).where(
            ImageModel.target_id == character.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER,
        )
    )
    existing_images = list(existing_img_result.scalars().all())
    if existing_images:
        print(
            f"[render_character] {len(existing_images)} render(s) already exist for this character"
        )
        for img in existing_images:
            print(
                f"  • image_id={img.id}  object_key={img.object_key!r}  bucket={img.bucket!r}"
            )

    # --- Always call render (creates a new variation) -------------------------
    print(f"[render_character] Calling POST .../character/{character.id}/render ...")

    response = await client.post(
        f"{BASE}/character/{character.id}/render",
        headers=headers,
    )

    print(f"[render_character] HTTP {response.status_code}")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert "id" in body, "Response missing 'id' field"
    assert "canonicalRender" in body, "Response missing 'canonicalRender' field"
    assert body["canonicalRender"] is not None, "canonicalRender should not be null"
    canonical = body["canonicalRender"]
    assert "id" in canonical, "canonicalRender missing 'id'"
    assert "objectKey" in canonical, "canonicalRender missing 'objectKey'"

    print("[render_character] Render succeeded:")
    print(f"  image_id   = {canonical['id']}")
    print(f"  objectKey  = {canonical['objectKey']!r}")
    print(f"  bucket     = {canonical.get('bucket')!r}")

    image_id = uuid.UUID(canonical["id"])

    # --- DB: image row -------------------------------------------------------
    img_result = await db.execute(select(ImageModel).where(ImageModel.id == image_id))
    image_row = img_result.scalar_one_or_none()
    assert image_row is not None, f"No image row found for id={image_id}"
    assert image_row.target_id == character.id, (
        f"image.target_id {image_row.target_id} != character.id {character.id}"
    )
    assert image_row.discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER, (
        f"Wrong discriminator_key: {image_row.discriminator_key!r}"
    )
    assert image_row.object_key, "image.object_key is empty"
    assert image_row.bucket, "image.bucket is empty"
    assert image_row.size_bytes > 0, "image.size_bytes should be > 0"

    print("\n[render_character] DB image row verified:")
    print(f"  target_id        = {image_row.target_id}")
    print(f"  discriminator    = {image_row.discriminator_key}")
    print(f"  object_key       = {image_row.object_key!r}")
    print(f"  bucket           = {image_row.bucket!r}")
    print(f"  size_bytes       = {image_row.size_bytes}")
    print(f"  content_type     = {image_row.content_type!r}")

    # --- DB: edit_event row --------------------------------------------------
    evt_result = await db.execute(
        select(EditEvent).where(
            EditEvent.target_id == character.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_CHARACTER,
            EditEvent.output_snapshot["image_id"].as_string() == str(image_id),
        )
    )
    event = evt_result.scalar_one_or_none()
    assert event is not None, (
        f"No edit_event found for render_character on character {character.id} "
        f"with image_id={image_id}"
    )
    assert event.status == EditEventStatus.SUCCEEDED, (
        f"edit_event status is {event.status!r}, expected 'succeeded'"
    )
    assert event.output_snapshot is not None, "edit_event.output_snapshot is None"
    assert event.output_snapshot.get("image_id") == str(image_id), (
        f"output_snapshot.image_id mismatch: {event.output_snapshot}"
    )

    print("\n[render_character] DB edit_event row verified:")
    print(f"  event_id         = {event.id}")
    print(f"  operation_type   = {event.operation_type}")
    print(f"  status           = {event.status}")
    print(f"  output_snapshot  = {event.output_snapshot}")


# ---------------------------------------------------------------------------
# Test 3 — Extract panels
# ---------------------------------------------------------------------------


@pytest.mark.manual
async def test_integration_extract_panels(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """
    POST /panels/generate — bulk-extract panels from the live story via OpenAI/instructor.

    Idempotent: if panels already exist we skip the POST and log them.

    DB asserts after extraction:
      - At least 1 panel row with story_id == STORY_ID
      - order_index values are sequential starting from 0
      - Each panel has an EditEvent(generate_panel, succeeded)
      - panel_character join rows exist (characters linked to panels)
    """
    headers = _auth_headers()

    # --- Check existing panels -----------------------------------------------
    existing_result = await db.execute(
        select(Panel).where(Panel.story_id == STORY_ID).order_by(Panel.order_index)
    )
    existing = list(existing_result.scalars().all())

    if existing:
        print(
            f"\n[extract_panels] {len(existing)} panel(s) already exist — skipping POST"
        )
        for p in existing:
            bg = (p.attributes or {}).get("background", "?")
            print(f"  • [{p.order_index}] id={p.id}  background={bg!r}")
    else:
        print("\n[extract_panels] No panels found — calling POST .../panels/generate")

        response = await client.post(f"{BASE}/panels/generate", headers=headers)

        print(f"[extract_panels] HTTP {response.status_code}")
        assert response.status_code == 201, (
            f"Expected 201, got {response.status_code}: {response.text}"
        )

        body = response.json()
        assert isinstance(body, list), "Response body should be a list"
        assert len(body) >= 1, "Expected at least 1 panel to be extracted"

        print(f"[extract_panels] Extracted {len(body)} panel(s):")
        for p in body:
            print(
                f"  • [{p['orderIndex']}] id={p['id']}  background={p.get('attributes', {}).get('background', '?')!r}"
            )

    # --- DB assertions -------------------------------------------------------
    await db.execute(text("SELECT 1"))

    db_result = await db.execute(
        select(Panel).where(Panel.story_id == STORY_ID).order_by(Panel.order_index)
    )
    db_panels = list(db_result.scalars().all())

    assert len(db_panels) >= 1, "Expected at least 1 panel row in DB"

    # order_index must be sequential from 0
    order_indices = [p.order_index for p in db_panels]
    assert order_indices == list(range(len(db_panels))), (
        f"order_index values are not sequential: {order_indices}"
    )

    print(f"\n[extract_panels] DB verified: {len(db_panels)} panel row(s) confirmed")

    for panel in db_panels:
        assert panel.story_id == STORY_ID, f"Panel {panel.id} has wrong story_id"
        assert isinstance(panel.attributes, dict), (
            f"Panel {panel.id} attributes is not a dict"
        )

        bg = (panel.attributes or {}).get("background", "?")
        dialogue = (panel.attributes or {}).get("dialogue", "?")
        print(f"  DB • [{panel.order_index}] id={panel.id}")
        print(f"         background = {bg!r}")
        print(f"         dialogue   = {dialogue!r}")

        # Each panel should have an EditEvent(generate_panel, succeeded)
        evt_result = await db.execute(
            select(EditEvent).where(
                EditEvent.target_type == EditEventTargetType.PANEL,
                EditEvent.target_id == panel.id,
                EditEvent.operation_type == EditEventOperationType.GENERATE_PANEL,
            )
        )
        event = evt_result.scalar_one_or_none()
        assert event is not None, (
            f"No generate_panel EditEvent found for panel {panel.id}"
        )
        assert event.status == EditEventStatus.SUCCEEDED, (
            f"Panel {panel.id} EditEvent status is {event.status!r}"
        )
        assert event.output_snapshot is not None, (
            f"Panel {panel.id} EditEvent has no output_snapshot"
        )
        assert "background" in event.output_snapshot, (
            f"Panel {panel.id} output_snapshot missing 'background'"
        )
        print(f"         edit_event = {event.id}  status={event.status}")

    # panel_character join rows — at least some panels should have characters linked
    total_joins = 0
    for panel in db_panels:
        join_result = await db.execute(
            select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
        )
        joins = list(join_result.scalars().all())
        total_joins += len(joins)
        if joins:
            char_ids = [str(j.character_id) for j in joins]
            print(f"  panel [{panel.order_index}] linked characters: {char_ids}")

    print(f"\n[extract_panels] Total panel_character join rows: {total_joins}")


# ---------------------------------------------------------------------------
# Test 4 — Render panel
# ---------------------------------------------------------------------------


@pytest.mark.manual
async def test_integration_render_panel(
    client: AsyncClient,
    db: AsyncSession,
) -> None:
    """
    POST /panel/{id}/render — render the first panel via fal + GCS.

    Uses the first panel (order_index=0) found in the DB for this story.

    DB asserts after rendering:
      - An image row with target_id == panel_id, discriminator_key == panel_render
      - An edit_event row with operation_type == render_panel, status == succeeded
      - output_snapshot contains {"image_id": "<uuid>"}
    """
    headers = _auth_headers()

    # Fetch panels from DB (ordered by order_index)
    panel_result = await db.execute(
        select(Panel).where(Panel.story_id == STORY_ID).order_by(Panel.order_index)
    )
    panels = list(panel_result.scalars().all())
    assert len(panels) >= 1, (
        "No panels found in DB — run test_integration_extract_panels first"
    )

    panel = panels[0]
    bg = (panel.attributes or {}).get("background", "?")
    print(
        f"\n[render_panel] Using panel: order_index={panel.order_index}  id={panel.id}"
    )
    print(f"[render_panel]   background = {bg!r}")

    # --- Check for existing panel renders ------------------------------------
    existing_img_result = await db.execute(
        select(ImageModel).where(
            ImageModel.target_id == panel.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.PANEL_RENDER,
        )
    )
    existing_images = list(existing_img_result.scalars().all())
    if existing_images:
        print(
            f"[render_panel] {len(existing_images)} render(s) already exist for this panel"
        )
        for img in existing_images:
            print(
                f"  • image_id={img.id}  object_key={img.object_key!r}  bucket={img.bucket!r}"
            )

    # --- Always call render (creates a new variation) -------------------------
    print(f"[render_panel] Calling POST .../panel/{panel.id}/render ...")

    response = await client.post(
        f"{BASE}/panel/{panel.id}/render",
        headers=headers,
    )

    print(f"[render_panel] HTTP {response.status_code}")
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert "id" in body, f"Response missing 'id' field. Body: {body}"

    image_id = uuid.UUID(body["id"])
    print("[render_panel] Render succeeded:")
    print(f"  image_id   = {image_id}")
    print(f"  objectKey  = {body.get('objectKey')!r}")
    print(f"  bucket     = {body.get('bucket')!r}")

    # --- DB: image row -------------------------------------------------------
    img_result = await db.execute(select(ImageModel).where(ImageModel.id == image_id))
    image_row = img_result.scalar_one_or_none()
    assert image_row is not None, f"No image row found for id={image_id}"
    assert image_row.target_id == panel.id, (
        f"image.target_id {image_row.target_id} != panel.id {panel.id}"
    )
    assert image_row.discriminator_key == ImageDiscriminatorKey.PANEL_RENDER, (
        f"Wrong discriminator_key: {image_row.discriminator_key!r}"
    )
    assert image_row.object_key, "image.object_key is empty"
    assert image_row.bucket, "image.bucket is empty"
    assert image_row.size_bytes > 0, "image.size_bytes should be > 0"

    print("\n[render_panel] DB image row verified:")
    print(f"  target_id        = {image_row.target_id}")
    print(f"  discriminator    = {image_row.discriminator_key}")
    print(f"  object_key       = {image_row.object_key!r}")
    print(f"  bucket           = {image_row.bucket!r}")
    print(f"  size_bytes       = {image_row.size_bytes}")
    print(f"  content_type     = {image_row.content_type!r}")

    # --- DB: edit_event row --------------------------------------------------
    evt_result = await db.execute(
        select(EditEvent).where(
            EditEvent.target_id == panel.id,
            EditEvent.operation_type == EditEventOperationType.RENDER_PANEL,
            EditEvent.output_snapshot["image_id"].as_string() == str(image_id),
        )
    )
    event = evt_result.scalar_one_or_none()
    assert event is not None, (
        f"No edit_event found for render_panel on panel {panel.id} "
        f"with image_id={image_id}"
    )
    assert event.status == EditEventStatus.SUCCEEDED, (
        f"edit_event status is {event.status!r}, expected 'succeeded'"
    )
    assert event.output_snapshot is not None, "edit_event.output_snapshot is None"
    assert event.output_snapshot.get("image_id") == str(image_id), (
        f"output_snapshot.image_id mismatch: {event.output_snapshot}"
    )

    print("\n[render_panel] DB edit_event row verified:")
    print(f"  event_id         = {event.id}")
    print(f"  operation_type   = {event.operation_type}")
    print(f"  status           = {event.status}")
    print(f"  output_snapshot  = {event.output_snapshot}")

    # --- Summary -------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"PIPELINE SUMMARY for story {STORY_ID}")
    print(f"{'=' * 60}")

    char_result = await db.execute(
        select(Character).where(Character.story_id == STORY_ID)
    )
    all_chars = list(char_result.scalars().all())
    print(f"Characters : {len(all_chars)}")
    for c in all_chars:
        print(f"  • {c.name!r} (id={c.id}, slug={c.slug!r})")

    panel_result2 = await db.execute(
        select(Panel).where(Panel.story_id == STORY_ID).order_by(Panel.order_index)
    )
    all_panels = list(panel_result2.scalars().all())
    print(f"Panels     : {len(all_panels)}")
    for p in all_panels:
        render_result = await db.execute(
            select(ImageModel).where(
                ImageModel.target_id == p.id,
                ImageModel.discriminator_key == ImageDiscriminatorKey.PANEL_RENDER,
            )
        )
        renders = list(render_result.scalars().all())
        print(f"  • [{p.order_index}] id={p.id}  renders={len(renders)}")

    char_render_result = await db.execute(
        select(ImageModel).where(
            ImageModel.discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER,
            ImageModel.target_id.in_([c.id for c in all_chars]),
        )
    )
    char_renders = list(char_render_result.scalars().all())
    print(f"Char renders: {len(char_renders)}")
    print(f"{'=' * 60}")
