"""
GCS object key factory for story engine assets.

All storage paths are rooted at:
    {user_id}/{project_id}/{story_id}/...

The private prefix chain means that changing the root structure requires
editing exactly one function (_story_prefix), and all public key builders
update automatically.

Every key includes the edit_event_id as the terminal segment so any blob in
GCS is directly traceable to the edit event that produced it.

Public API
----------
character_render_key    — fal render for a character
character_reference_key — user-uploaded reference image for a character
panel_render_key        — fal render for a panel
panel_reference_key     — user-uploaded reference image for a panel
"""

import uuid

# ── Private prefix chain ──────────────────────────────────────────────────────


def _story_prefix(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
) -> str:
    return f"{user_id}/{project_id}/{story_id}"


# ── Public key builders ───────────────────────────────────────────────────────


def character_render_key(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_id: uuid.UUID,
    edit_event_id: uuid.UUID,
) -> str:
    """Key for a character render produced by fal and stored in GCS."""
    prefix = _story_prefix(user_id, project_id, story_id)
    return f"{prefix}/character/{character_id}/renders/{edit_event_id}"


def character_reference_key(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    character_slug: str,
    edit_event_id: uuid.UUID,
) -> str:
    """Key for a user-uploaded reference image for a character."""
    prefix = _story_prefix(user_id, project_id, story_id)
    return f"{prefix}/character/{character_slug}/references/{edit_event_id}"


def panel_render_key(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    edit_event_id: uuid.UUID,
) -> str:
    """Key for a panel render produced by fal and stored in GCS."""
    prefix = _story_prefix(user_id, project_id, story_id)
    return f"{prefix}/panel/{panel_id}/renders/{edit_event_id}"


def panel_reference_key(
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    story_id: uuid.UUID,
    panel_id: uuid.UUID,
    edit_event_id: uuid.UUID,
) -> str:
    """Key for a user-uploaded reference image for a panel."""
    prefix = _story_prefix(user_id, project_id, story_id)
    return f"{prefix}/panel/{panel_id}/references/{edit_event_id}"
