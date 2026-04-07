"""
Unit tests for core/story_engine/storage_keys.py

Invariants:
  1. All keys are rooted at {user_id}/{project_id}/{story_id}
  2. Each key type produces the correct sub-path
  3. All keys are deterministic — same inputs always produce the same key
  4. Changing _story_prefix cascades to all public functions (structural test)
"""

import uuid

from core.story_engine.storage_keys import (
    _story_prefix,
    character_reference_key,
    character_render_key,
    panel_reference_key,
    panel_render_key,
)

# Shared fixture UUIDs — fixed so tests are deterministic
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROJECT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
STORY_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
CHARACTER_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")
PANEL_ID = uuid.UUID("00000000-0000-0000-0000-000000000005")
EDIT_EVENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000006")
CHARACTER_SLUG = "aragorn"

EXPECTED_PREFIX = f"{USER_ID}/{PROJECT_ID}/{STORY_ID}"


# ── Prefix chain ──────────────────────────────────────────────────────────────


def test_story_prefix_structure() -> None:
    """_story_prefix produces user/project/story."""
    result = _story_prefix(USER_ID, PROJECT_ID, STORY_ID)
    assert result == EXPECTED_PREFIX


# ── character_render_key ──────────────────────────────────────────────────────


def test_character_render_key_starts_with_story_prefix() -> None:
    key = character_render_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_ID, EDIT_EVENT_ID
    )
    assert key.startswith(EXPECTED_PREFIX + "/")


def test_character_render_key_structure() -> None:
    key = character_render_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_ID, EDIT_EVENT_ID
    )
    expected = f"{EXPECTED_PREFIX}/character/{CHARACTER_ID}/renders/{EDIT_EVENT_ID}"
    assert key == expected


def test_character_render_key_is_deterministic() -> None:
    key_a = character_render_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_ID, EDIT_EVENT_ID
    )
    key_b = character_render_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_ID, EDIT_EVENT_ID
    )
    assert key_a == key_b


# ── character_reference_key ───────────────────────────────────────────────────


def test_character_reference_key_starts_with_story_prefix() -> None:
    key = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, EDIT_EVENT_ID
    )
    assert key.startswith(EXPECTED_PREFIX + "/")


def test_character_reference_key_structure() -> None:
    key = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, EDIT_EVENT_ID
    )
    expected = (
        f"{EXPECTED_PREFIX}/character/{CHARACTER_SLUG}/references/{EDIT_EVENT_ID}"
    )
    assert key == expected


def test_character_reference_key_is_deterministic() -> None:
    key_a = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, EDIT_EVENT_ID
    )
    key_b = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, EDIT_EVENT_ID
    )
    assert key_a == key_b


# ── panel_render_key ──────────────────────────────────────────────────────────


def test_panel_render_key_starts_with_story_prefix() -> None:
    key = panel_render_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    assert key.startswith(EXPECTED_PREFIX + "/")


def test_panel_render_key_structure() -> None:
    key = panel_render_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    expected = f"{EXPECTED_PREFIX}/panel/{PANEL_ID}/renders/{EDIT_EVENT_ID}"
    assert key == expected


def test_panel_render_key_is_deterministic() -> None:
    key_a = panel_render_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    key_b = panel_render_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    assert key_a == key_b


# ── panel_reference_key ───────────────────────────────────────────────────────


def test_panel_reference_key_starts_with_story_prefix() -> None:
    key = panel_reference_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    assert key.startswith(EXPECTED_PREFIX + "/")


def test_panel_reference_key_structure() -> None:
    key = panel_reference_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    expected = f"{EXPECTED_PREFIX}/panel/{PANEL_ID}/references/{EDIT_EVENT_ID}"
    assert key == expected


def test_panel_reference_key_is_deterministic() -> None:
    key_a = panel_reference_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    key_b = panel_reference_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID)
    assert key_a == key_b


# ── Cascade test — structural ─────────────────────────────────────────────────


def test_all_public_keys_share_same_prefix() -> None:
    """All four public functions produce keys rooted at the same prefix.

    This confirms the prefix chain is working: _story_prefix is the single
    source of truth and all public builders delegate to it.
    """
    prefix = _story_prefix(USER_ID, PROJECT_ID, STORY_ID)

    keys = [
        character_render_key(
            USER_ID, PROJECT_ID, STORY_ID, CHARACTER_ID, EDIT_EVENT_ID
        ),
        character_reference_key(
            USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, EDIT_EVENT_ID
        ),
        panel_render_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID),
        panel_reference_key(USER_ID, PROJECT_ID, STORY_ID, PANEL_ID, EDIT_EVENT_ID),
    ]

    for key in keys:
        assert key.startswith(prefix + "/"), (
            f"Key '{key}' does not start with prefix '{prefix}/'"
        )


def test_different_stories_produce_different_keys() -> None:
    """Keys for different story IDs are distinct — no collision across stories."""
    story_a = uuid.uuid4()
    story_b = uuid.uuid4()

    key_a = panel_render_key(USER_ID, PROJECT_ID, story_a, PANEL_ID, EDIT_EVENT_ID)
    key_b = panel_render_key(USER_ID, PROJECT_ID, story_b, PANEL_ID, EDIT_EVENT_ID)

    assert key_a != key_b


def test_different_edit_events_produce_different_keys() -> None:
    """Different edit_event_ids produce different keys — no collision across events."""
    eid_a = uuid.uuid4()
    eid_b = uuid.uuid4()

    key_a = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, eid_a
    )
    key_b = character_reference_key(
        USER_ID, PROJECT_ID, STORY_ID, CHARACTER_SLUG, eid_b
    )

    assert key_a != key_b
