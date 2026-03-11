# Agent Context — Backend Testing

## Philosophy

API-level tests first, expand inward (service, repository) only when needed. Full stack, real Postgres, no mocking.

Do not change shared `core/services/*` infrastructure or broaden fixes across layers without explicit user approval. Keep changes inside the requested feature area unless the user asks for a wider refactor.

Async SQLAlchemy guardrails:
- Fixture session settings do not automatically apply to FastAPI request-scoped sessions.
- Treat ORM instances as short-lived in async request flows.
- Do not rely on ORM-loaded attributes after a commit; implicit lazy refresh can trigger hidden I/O and `MissingGreenlet` errors.
- Before a commit, snapshot any scalar or JSON values you still need; otherwise issue a fresh awaited query after the commit.
- Prefer explicit re-queries or single-transaction flows over mid-request commits that leave later code depending on expired ORM state.

## Stack

- `pytest` + `pytest-asyncio` + `httpx`
- `AsyncClient` talks to the real `fastapi_app` in-process
- Real local Postgres via `.env.local`

## Fixture chain

```
db_session → user → project → story → character
```

Defined in `tests/conftest.py`. Each fixture creates a real DB row and cleans up via raw SQL on teardown. Tests declare only what they need — pytest builds the chain.

## Key files

- `tests/conftest.py` — all shared fixtures
- `tests/story_engine/test_character_api.py` — character endpoint tests (GET, PATCH, DELETE)
- `pyproject.toml [tool.pytest.ini_options]` — asyncio mode, testpaths, warning filters

## Expanding

- **New API tests** — add to an existing file or create `tests/<module>/test_<feature>_api.py`
- **Service/repo tests** — add a `service`/`repository` fixture to `conftest.py`, create the corresponding test file
- **New fixtures** — add to `conftest.py`, follow the `yield` + raw SQL teardown pattern
- **Manual smoke tests** — use these only for iterative development when you need to hit existing rows or external services. Drive them with explicit env vars, mark them `@pytest.mark.manual`, and keep them out of the normal self-cleaning fixture flow.

## Running

```bash
uv run pytest                                                                        # all
uv run pytest tests/story_engine/test_character_api.py -v                           # one file
uv run pytest tests/story_engine/test_character_api.py::test_get_character_200 -v   # one test
```
