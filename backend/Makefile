.PHONY: lint typecheck check format

lint:
	ruff check .
	ruff format --check .

typecheck:
	mypy .

check: lint typecheck

format:
	ruff format .
	ruff check --fix .