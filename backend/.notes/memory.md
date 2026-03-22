# Tooling

- **uv** for env management. Python at `.venv/bin/python` or run with `uv run`.
- **ruff** for formatting/linting, **mypy** for static typing. Run `make format-check` after making changes.

# Follow-ups

Relevant when building query/service layers or API endpoints that load project state.

1. **N+1 on 1:many stories** — Project now has multiple stories. Any code that iterates `project.stories` and accesses `story.characters` or `story.panels` will fire a separate query per story (lazy loading). Use `selectinload` to batch-load in 2-3 queries total.
2. **Cross-story panel ordering** — `panel_order` is unique per-story, not per-project. If a UI ever flattens panels across all stories in a project, the ordering depends on story traversal order (undefined). Add explicit ordering (e.g. `story_order` on Story, or `global_order` on ComicPanel) only if that need arises.
