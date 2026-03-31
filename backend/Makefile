.PHONY: lint typecheck check format

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run mypy .

check: lint typecheck

format:
	uv run ruff check --fix .
	uv run ruff format .

format-check: format check
