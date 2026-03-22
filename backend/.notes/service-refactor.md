# Split Service into Domain Services

## Context

`service.py` is a 600+ line god-object with 4 domains crammed into one class. After cleanly splitting the repository layer into domain repos, the service layer should follow the same pattern: one file per domain, direct injection into routers, no facade.

## Design Decisions

- **No facade class.** Routers inject domain services directly — no `Service` wrapper re-delegating.
- **No inter-service calls.** Cross-domain reads (e.g., character methods validating story exists) go through `repository_v2.story` directly. The repository layer is the shared read interface.
- **Story CRUD stays in ProjectService.** `create_story` and `delete_story` are project-scoped operations and live in the `projects.py` router, so they belong in `ProjectService` to keep that router injecting one service.
- **Render/upload stays in CharacterService.** These are character-scoped operations. If they grow, they can be extracted later.
- **Streaming classes stay in `story_service.py`.** `StoryStreamGenerator`, `OpenAIStreamProcessor`, `StoryStreamContext` are only used by story generation (~60 lines). No need for a separate file yet.

## Target Structure

```
service/
├── __init__.py              # exports ProjectService, StoryService, CharacterService
├── project_service.py       # ~50 lines
├── story_service.py         # ~180 lines (includes streaming classes)
├── character_service.py     # ~280 lines (includes render + upload delegation)
├── image_upload.py          # unchanged
└── dto_types.py             # unchanged
```

## Method Mapping

### `ProjectService` (`project_service.py`)
| Method | Type |
|--------|------|
| `get_all_projects_of_user` | read → `repository_v2.project` |
| `create_project` | write → `repository` |
| `get_project_details` | read → `repository_v2.project` |
| `create_story` | write → `repository` |
| `delete_story` | write → `repository` |

Constructor: `(db_session, repository=None)`

### `StoryService` (`story_service.py`)
| Method | Type |
|--------|------|
| `get_story` | read → `repository_v2.story` |
| `get_story_history` | read → `repository_v2.edit_event` |
| `generate_story` | orchestration: ownership check → prompt → stream → persist |
| `_execute_streaming` | internal async generator |
| `_get_user_id` | private helper |
| `_check_story_ownership` | private helper |
| `_build_refinement_prompt` | private helper |

Module-level classes: `StoryStreamGenerator`, `StreamProcessor`, `OpenAIStreamProcessor`, `StoryStreamContext`

Constructor: `(db_session, repository=None, stream_generator=None, processor=None)`

### `CharacterService` (`character_service.py`)
| Method | Type |
|--------|------|
| `get_character_history` | read → `repository_v2.edit_event` |
| `get_story_characters` | read (validates story via `repository_v2.story`) |
| `get_character` | read |
| `extract_characters_from_story` | LLM extraction → bulk create |
| `update_character` | write → `repository` |
| `refine_character` | orchestration: LLM refinement → persist |
| `delete_character` | write → `repository` |
| `render_character` | FAL image gen → persist |
| `upload_reference_image` | delegates to `ImageUploadService` |
| `_extract_characters_from_story` | LLM helper |
| `_refine_character_profile` | LLM helper |
| `_build_character_refinement_prompt` | private helper |
| `_build_character_render_prompt` | private helper |
| `_generate_image_render_response_and_time` | FAL helper |
| `_get_character_url_from_fal_client_response` | response parser |

Constructor: `(db_session, repository=None, image_upload_service=None)`

## Files to Modify

| File | Change |
|------|--------|
| `service/project_service.py` | **create** |
| `service/story_service.py` | **create** |
| `service/character_service.py` | **create** |
| `service/__init__.py` | export 3 domain services |
| `api/dependencies.py` | add `get_project_service`, `get_story_service`, `get_character_service`; remove `get_service` |
| `api/v2/projects.py` | `Service` → `ProjectService` |
| `api/v2/story.py` | `Service` → `StoryService` |
| `api/v2/character.py` | `Service` → `CharacterService` |
| `service/service.py` | **delete** |

## Execution Steps

1. Create the 3 domain service files with methods moved from `service.py`
2. Update `__init__.py` to export new services (keep `Service` temporarily for compat)
3. Add new factory functions to `dependencies.py`
4. Update `v2/projects.py` → `ProjectService`
5. Update `v2/story.py` → `StoryService`
6. Update `v2/character.py` → `CharacterService`
7. Remove old `service.py` and `get_service` from dependencies
8. Run tests, lint, mypy

Single commit: `refactor(story-engine): split Service into ProjectService, StoryService, CharacterService`

## Verification

- `python -m pytest tests/story_engine/ -v -m "not manual"` — all tests pass
- `ruff check core/story_engine/` — clean
- `ruff format --check core/story_engine/` — clean
- `grep -r "from ...service import Service" core/story_engine/api/` — no matches (old import gone)
- `grep -r "get_service" core/story_engine/api/` — no matches (old factory gone)
