# Agent Context — Backend Testing

## Philosophy

API-level tests first, expand inward (service, repository) only when needed. Full stack, real Postgres, no mocking.

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

## Running

```bash
uv run pytest                                                                        # all
uv run pytest tests/story_engine/test_character_api.py -v                           # one file
uv run pytest tests/story_engine/test_character_api.py::test_get_character_200 -v   # one test
```
