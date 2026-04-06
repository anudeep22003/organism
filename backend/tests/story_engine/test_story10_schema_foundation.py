"""
Story 10 test gate — Schema foundation: image table migration, panel tables,
enum additions, fix render_character.

Test invariants verified here:
  1. upload_reference_image creates an Image row with target_id=character_id,
     discriminator_key=character_reference, and output_snapshot contains
     {"image_id": "<uuid>"}.
  2. render_character creates an Image row with target_id=character_id,
     discriminator_key=character_render. character.render_url is NOT updated.
  3. Calling render_character twice creates two Image rows for the same
     character (variation tracking).
  4. A Panel can be created and persisted with story_id, order_index,
     attributes.
  5. panel_character rows cascade-delete when the panel is deleted.
  6. Deleting a Story cascade-deletes its panels and panel_character rows.
"""

import io
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.models.user import User
from core.story_engine.models import Character, Panel, Project, Story
from core.story_engine.models import Image as ImageModel
from core.story_engine.models.edit_event import (
    EditEventOperationType,
    EditEventStatus,
)
from core.story_engine.models.image import ImageDiscriminatorKey
from core.story_engine.models.panel_character import PanelCharacter
from core.story_engine.repository import RepositoryV2
from core.story_engine.service.character_service import CharacterService
from core.story_engine.service.image_service import ImageService, StorageReceipt

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_jpeg() -> io.BytesIO:
    """Return a tiny valid 1×1 JPEG byte stream for upload tests."""
    # A minimal valid JPEG: SOI + APP0 + SOF0 + SOS + EOI
    # Using a simpler approach: create via Pillow

    from PIL import Image as PILImage

    buf = BytesIO()
    PILImage.new("RGB", (10, 10), color=(255, 0, 0)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# upload_reference_image tests
# ---------------------------------------------------------------------------


async def test_upload_reference_image_creates_image_row_with_target_id(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Image row uses target_id (not character_id FK) and correct discriminator."""
    repo = RepositoryV2(db_session)

    mock_receipt = StorageReceipt(
        object_key=f"{user.id}/character/{character.slug}/references/test-key",
        bucket="test-bucket",
    )

    with patch(
        "core.story_engine.service.image_service.GCSUploadService.upload",
        return_value=mock_receipt,
    ):
        service = ImageService(db=db_session, repository_v2=repo)
        image = await service.upload_character_reference_image(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
            image_byte_stream=_make_minimal_jpeg(),
        )

    await db_session.refresh(image)

    # target_id must point to character.id
    assert image.target_id == character.id
    assert image.discriminator_key == ImageDiscriminatorKey.CHARACTER_REFERENCE
    assert image.project_id == project.id
    assert image.user_id == user.id


async def test_upload_reference_image_output_snapshot_contains_image_id(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """output_snapshot on the EditEvent contains {"image_id": "<uuid>"} (Decision 7)."""
    from core.story_engine.models import EditEvent

    repo = RepositoryV2(db_session)

    mock_receipt = StorageReceipt(
        object_key=f"{user.id}/character/{character.slug}/references/test-key",
        bucket="test-bucket",
    )

    with patch(
        "core.story_engine.service.image_service.GCSUploadService.upload",
        return_value=mock_receipt,
    ):
        service = ImageService(db=db_session, repository_v2=repo)
        image = await service.upload_character_reference_image(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
            image_byte_stream=_make_minimal_jpeg(),
        )

    # Fetch the EditEvent created during this operation
    event_result = await db_session.execute(
        select(EditEvent)
        .where(
            EditEvent.target_id == character.id,
            EditEvent.operation_type == EditEventOperationType.UPLOAD_REFERENCE_IMAGE,
        )
        .order_by(EditEvent.created_at.desc())
        .limit(1)
    )
    event = event_result.scalar_one_or_none()
    assert event is not None
    assert event.status == EditEventStatus.SUCCEEDED
    assert event.output_snapshot is not None
    assert "image_id" in event.output_snapshot
    assert event.output_snapshot["image_id"] == str(image.id)


# ---------------------------------------------------------------------------
# render_character tests
# ---------------------------------------------------------------------------


def _mock_fal_response(url: str = "https://fal.ai/render/test-image.jpg") -> dict:
    return {"images": [{"url": url}]}


async def test_render_character_creates_image_row_with_character_render_discriminator(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """render_character creates an Image row with discriminator=character_render."""
    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/character/{character.id}/renders/test-key",
        bucket="test-bucket",
    )
    fake_image_bytes = _make_minimal_jpeg().read()

    with (
        patch(
            "core.story_engine.service.character_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.character_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.character_service.httpx.AsyncClient",
        ) as mock_httpx_cls,
    ):
        mock_resp = MagicMock()
        mock_resp.content = fake_image_bytes
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_ctx = AsyncMock()
        mock_httpx_ctx.__aenter__ = AsyncMock(return_value=mock_httpx_ctx)
        mock_httpx_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_ctx.get = AsyncMock(return_value=mock_resp)
        mock_httpx_cls.return_value = mock_httpx_ctx

        service = CharacterService(db_session=db_session)
        returned_character, returned_image = await service.render_character(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
        )

    # Verify Image row
    result = await db_session.execute(
        select(ImageModel).where(
            ImageModel.target_id == character.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER,
        )
    )
    images = list(result.scalars().all())
    assert len(images) == 1
    assert images[0].target_id == character.id
    assert images[0].discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER


async def test_render_character_does_not_update_render_url(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """render_url on Character stays null after render_character (Decision 5)."""
    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/character/{character.id}/renders/test-key",
        bucket="test-bucket",
    )
    fake_image_bytes = _make_minimal_jpeg().read()

    with (
        patch(
            "core.story_engine.service.character_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.character_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.character_service.httpx.AsyncClient",
        ) as mock_httpx_cls,
    ):
        mock_resp = MagicMock()
        mock_resp.content = fake_image_bytes
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_ctx = AsyncMock()
        mock_httpx_ctx.__aenter__ = AsyncMock(return_value=mock_httpx_ctx)
        mock_httpx_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_ctx.get = AsyncMock(return_value=mock_resp)
        mock_httpx_cls.return_value = mock_httpx_ctx

        service = CharacterService(db_session=db_session)
        returned_character, _ = await service.render_character(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
        )

    await db_session.refresh(returned_character)
    # render_url must stay null — the image table is the source of truth (Decision 5)
    assert returned_character.render_url is None


async def test_render_character_twice_creates_two_image_rows(
    db_session: AsyncSession,
    user: User,
    project: Project,
    story: Story,
    character: Character,
) -> None:
    """Two render calls create two separate Image rows (variation tracking, Decision 6)."""
    mock_receipt = StorageReceipt(
        object_key=f"{project.id}/character/{character.id}/renders/test-key",
        bucket="test-bucket",
    )
    fake_image_bytes = _make_minimal_jpeg().read()

    def _make_mock_httpx() -> AsyncMock:
        mock_resp = MagicMock()
        mock_resp.content = fake_image_bytes
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.raise_for_status = MagicMock()
        mock_httpx_ctx = AsyncMock()
        mock_httpx_ctx.__aenter__ = AsyncMock(return_value=mock_httpx_ctx)
        mock_httpx_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_httpx_ctx.get = AsyncMock(return_value=mock_resp)
        return mock_httpx_ctx

    with (
        patch(
            "core.story_engine.service.character_service.fal_async_client.subscribe",
            new_callable=AsyncMock,
            return_value=_mock_fal_response(),
        ),
        patch(
            "core.story_engine.service.character_service.GCSUploadService.upload",
            return_value=mock_receipt,
        ),
        patch(
            "core.story_engine.service.character_service.httpx.AsyncClient",
            side_effect=[_make_mock_httpx(), _make_mock_httpx()],
        ),
    ):
        service = CharacterService(db_session=db_session)
        await service.render_character(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
        )
        await service.render_character(
            user_id=user.id,
            project_id=project.id,
            story_id=story.id,
            character_id=character.id,
        )

    result = await db_session.execute(
        select(ImageModel).where(
            ImageModel.target_id == character.id,
            ImageModel.discriminator_key == ImageDiscriminatorKey.CHARACTER_RENDER,
        )
    )
    images = list(result.scalars().all())
    assert len(images) == 2


# ---------------------------------------------------------------------------
# Panel model persistence tests
# ---------------------------------------------------------------------------


async def test_panel_can_be_created_and_persisted(
    db_session: AsyncSession,
    story: Story,
) -> None:
    """Panel.create() persists a row with the expected fields."""
    panel = Panel.create(
        story_id=story.id,
        order_index=0,
        attributes={"background": "A dark forest", "dialogue": "Hello world"},
    )
    db_session.add(panel)
    await db_session.commit()
    await db_session.refresh(panel)

    assert panel.id is not None
    assert panel.story_id == story.id
    assert panel.order_index == 0
    assert panel.attributes["background"] == "A dark forest"
    assert panel.attributes["dialogue"] == "Hello world"
    assert panel.source_event_id is None


async def test_panel_character_cascade_delete_on_panel_delete(
    db_session: AsyncSession,
    story: Story,
    character: Character,
) -> None:
    """panel_character rows are cascade-deleted when the parent panel is deleted."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()

    join_row = PanelCharacter(panel_id=panel.id, character_id=character.id)
    db_session.add(join_row)
    await db_session.commit()

    # Verify the join row exists
    result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    assert len(list(result.scalars().all())) == 1

    # Delete the panel
    await db_session.delete(panel)
    await db_session.commit()

    # Join row must be gone
    result2 = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel.id)
    )
    assert len(list(result2.scalars().all())) == 0


async def test_deleting_story_cascade_deletes_panels_and_panel_character(
    db_session: AsyncSession,
    project: Project,
    character: Character,
    story: Story,
) -> None:
    """Story delete cascades to panel and panel_character rows."""
    panel = Panel.create(story_id=story.id, order_index=0, attributes={})
    db_session.add(panel)
    await db_session.flush()
    panel_id = panel.id

    join_row = PanelCharacter(panel_id=panel_id, character_id=character.id)
    db_session.add(join_row)
    await db_session.commit()

    # Delete the story via raw SQL to trigger DB-level CASCADE without ORM interference
    # (The ORM would try to null out story_id on character before delete, which fails
    # the NOT NULL constraint. Raw SQL bypasses this, testing the actual DB cascade.)
    await db_session.execute(
        text("DELETE FROM story WHERE id = :story_id"), {"story_id": story.id}
    )
    await db_session.commit()

    # Both panel and join row must be gone
    panel_result = await db_session.execute(select(Panel).where(Panel.id == panel_id))
    assert panel_result.scalar_one_or_none() is None

    join_result = await db_session.execute(
        select(PanelCharacter).where(PanelCharacter.panel_id == panel_id)
    )
    assert len(list(join_result.scalars().all())) == 0
