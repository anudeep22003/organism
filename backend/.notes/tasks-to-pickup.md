# Tasks to Pickup

- [ ] Type hygiene: update repository method signatures to accept `uuid.UUID` for `user_id` (instead of `str`), and do string-to-UUID conversion only at API/service boundaries.
- [ ] Performance hygiene: add explicit Postgres indexes for FK columns used in joins/lookups (e.g., `character.story_id`, `story.project_id`, `project.user_id`) via model metadata/migrations.
- [ ] Module boundary cleanup: move service-layer exceptions used by `core/story_engine/service/service.py` into the service module/package to keep exception ownership aligned with the service layer.
- [ ] Service decomposition: split `core/story_engine/service/service.py` into smaller domain-oriented service modules (e.g., story, character, image/upload, streaming) with explicit interfaces/composition.
- [ ] Repository decomposition: split `core/story_engine/repository.py` into smaller domain-oriented repository modules (e.g., story, character, edit_event, project) while preserving transactional clarity and shared session handling.
- [ ] Dev/test ergonomics: add a CLI command (or equivalent utility) to generate JWT tokens for local/manual testing with configurable claims/expiry.
- [ ] Config cleanup: remove redundancy in `core/config.py` by consolidating env loading/validation into a typed config structure (e.g., `TypedDict` + shared validator/reader) to keep config explicit and DRY.
