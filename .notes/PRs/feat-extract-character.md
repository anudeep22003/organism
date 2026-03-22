# Extract & Manage Story Characters

**Branch:** `feat/extract-character` → `main`

---

## Summary

Introduces a full character lifecycle to the story engine — from AI-powered extraction out of story text, through manual and AI-assisted refinement, to image rendering via Fal. Characters are persisted as first-class entities with their own CRUD endpoints, edit-event history, and render pipeline.

---

## What changed

### New domain: `Character`

| Layer | Files |
|---|---|
| **Model** | `models/character.py` — UUID PK, JSONB `attributes` & `meta`, FK to `story` and optional FK to `edit_event` (source lineage), `render_url` |
| **Schema** | `schemas/character.py` — response, partial-update, and refine-request schemas |
| **Repository** | `repository.py` — bulk create, single get, list by story, partial-merge update, full-replace attributes, delete, render URL update |
| **Service** | `service.py` — orchestrates extraction, refinement, CRUD, and rendering |
| **API** | `api/v2/character.py` — 8 endpoints (see below) |

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `.../story/{id}/characters` | Extract characters from story text (GPT-4o → Instructor) |
| `GET` | `.../story/{id}/characters` | List all characters for a story |
| `GET` | `.../character/{id}` | Get a single character |
| `PATCH` | `.../character/{id}` | Partial update (merge into JSONB attributes) |
| `POST` | `.../character/{id}/refine` | AI-assisted refinement with edit-event tracking |
| `DELETE` | `.../character/{id}` | Delete a character |
| `GET` | `.../character/{id}/history` | Edit-event history for a character |
| `POST` | `.../character/{id}/render` | Generate character image via Fal, persist URL |

### Migrations

1. `new_character_table_for_extraction` — creates the `character` table
2. `add_url_field_to_character_table` — adds `render_url`
3. `add_character_source_event_id` — adds `source_event_id` FK to `edit_event`

### Edit-event integration

- `TargetType.CHARACTER` and `OperationType.REFINE_CHARACTER` added to the `EditEvent` enum
- Refinement creates a `PENDING` event with the current attributes as `input_snapshot`, calls GPT-4o via Instructor, replaces attributes, then marks the event `SUCCEEDED` (or `FAILED` on error)

### Test infrastructure

- **pytest + pytest-asyncio + httpx** added as dev dependencies with async auto-mode config
- `conftest.py` — fixture chain (`db_session → user → project → story → character`) with raw-SQL teardown to avoid ORM identity-map issues
- `test_character_api.py` — 9 automated tests covering GET/PATCH/DELETE happy paths and 404s
- `test_character_refine_smoke.py` — opt-in `@pytest.mark.manual` smoke tests for refinement, history, and rendering against a live DB row

### Minor cleanups

- Repository return types changed from `Sequence` → `list` for consistency
- `rows` renamed to `projects` in the projects endpoint for clarity
- SQLAlchemy session bug fix in a `try/finally` path

---

## How to test

```bash
# automated tests (needs local Postgres running)
cd backend && uv run pytest tests/story_engine/test_character_api.py -v

# manual smoke tests (needs seeded data + API keys)
cd backend && uv run pytest tests/story_engine/test_character_refine_smoke.py -v -m manual
```

---

## Notes

- Character attributes are stored as JSONB — the schema is enforced at the API/Instructor layer, not at the DB level, keeping it flexible for iteration.
- The `render_url` is currently a direct Fal CDN URL; no permanence guarantee — future work should copy to our own storage.
- Extraction replaces all characters for a story (additive `bulk_create`); there is no deduplication yet.
