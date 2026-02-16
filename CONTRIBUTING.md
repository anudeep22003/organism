# Contributing

Thanks for contributing.

This project has:
- `backend/`: FastAPI + Python (managed with `uv`)
- `frontend/`: React + TypeScript (managed with `npm`)

## Ground rules

- Keep PRs small and focused.
- Link issues when relevant.
- Be respectful in discussions.

## Git hooks

After cloning, install the pre-commit hook:

```bash
./scripts/install-hooks.sh
```

This sets up a hook that automatically runs checks on staged files before each commit:

- **Backend changes** → `make format-check` (auto-format + lint + typecheck)
- **Frontend changes** → `npm run lint` + `npm run type-check`

Only the relevant checks run based on which directories you changed.

## Local setup

### Backend

```bash
cd backend
uv sync --dev
```

Run checks:

```bash
uv run ruff check .
uv run mypy .
# Optional test placeholder:
# uv run pytest
```

### Frontend

```bash
cd frontend
npm ci
```

Run checks/build:

```bash
npm run type-check
npm run build
```

## Pull requests

1. Create a branch from `main`.
2. Make focused changes.
3. Run the relevant checks locally.
4. Open a PR using the template.

## CI expectations

Your PR should pass:
- Backend lint/type checks (`ruff`, `mypy`)
- Frontend type-check and build

## Reporting bugs and requesting features

Use the GitHub issue templates so reports are actionable and easy to triage.
