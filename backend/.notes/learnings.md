# Learnings

## SQLAlchemy: `viewonly=True` and Relationship Overlap Warnings

**Context:** When you define both a direct relationship to an association object (e.g., `Story.story_characters -> StoryCharacter`) and a `secondary` shortcut that skips over it (e.g., `Story.characters` via `secondary="story_character"`), SQLAlchemy warns that multiple relationships claim write access to the same foreign key columns on the join table.

**Why it matters:** If two relationships both think they can write to the same columns, SQLAlchemy's unit of work can produce conflicting or duplicate INSERTs/DELETEs during a flush — leading to integrity errors or silent data corruption.

**The fix:** Mark the `secondary` shortcut relationships as `viewonly=True`. These are read-only convenience accessors anyway — they skip the association object so they can't populate extra columns like `meta`. All writes to the join table should go through the direct association object relationships (e.g., `session.add(StoryCharacter(...))`).

**Why keep the direct association relationships writable:** Even if you never `append()` to them, their `cascade="all, delete-orphan"` keeps SQLAlchemy's in-memory session state consistent when you delete a parent. The DB-level `ondelete="CASCADE"` handles the actual row deletion regardless, but without ORM-level cascade, already-loaded child objects become stale in the identity map.

**Rule of thumb:** If a relationship exists purely for navigation convenience (especially `secondary` many-to-many shortcuts alongside association objects), it should be `viewonly=True`.

## SQLAlchemy ORM: relationship attributes, lazy loading, computed properties, counts, and typing

### Data you "get back" from `select(Model)`

- **Columns**: `select(Project)` hydrates **only the `project` table columns** into the `Project` object (e.g. `id`, `name`, `meta`, `state`).
- **Relationships**: `Project.stories` is **not automatically loaded**. It is typically **lazy-loaded** (extra SQL when accessed) unless you eager-load.
- **Computed properties**: `Project.characters` (a `@property`) is **not a DB field**; it is Python code that often **touches relationships** (which can trigger extra SQL).

### Eager loading: `options(...)` + `selectinload(...)` (avoid surprise IO / N+1)

- **`options(...)`** attaches ORM loader instructions to a `select(...)` (it doesn’t change the return type; it changes what relationships are preloaded).
- **`selectinload(A.rel)`** loads a collection in a follow-up `IN (...)` query, then populates `A.rel` in memory.
- **Chaining expresses a path**: `selectinload(Project.stories).selectinload(Story.panels)` means “prefetch `Project.stories`, then for those loaded `Story` rows prefetch `Story.panels`”.

**Spaced repetition checks**

- If you only ran `select(Project)`, do you have `Project.stories` already? **No** (unless eager-loaded).
- Is `@property characters` a column? **No** (it may cause relationship loads).

### Why counts should not load full relationships

- **Bad default**: `len(project.stories)` can trigger a lazy load of *all* stories (wasteful) and can become **N+1 queries** in a project list.
- **Good default**: ask the DB for the count:
  - **Left outer join + group-by** (includes projects with 0 stories)
  - **Correlated subquery** (also count-only; often simpler to read)

**Rule of thumb:** If the API needs a **count**, don’t load the **collection**.

### `scalars()` vs `all()` (the “dropped columns” gotcha)

- **`result.scalars()`**: returns **only the first selected element** from each row.
  - `select(Project)` → first element is `Project` → OK.
  - `select(Project, func.count(...))` → first element is `Project` → the count is **dropped**.
- **`result.all()`**: returns full rows (e.g. `[(Project, story_count), ...]`).
- **Best for typing/unpacking**: `result.tuples().all()` tells SQLAlchemy you want **plain tuples**, not `Row[...]`.

**Spaced repetition checks**

- When is `scalars()` safe? **Only when you selected one thing** (or you intentionally want just the first).
- What do you switch to when selecting multiple things? **`all()` / `tuples().all()`**.

### Pydantic mapping: ORM object != extra select columns

- `ProjectListResponseSchema.model_validate(project)` works only if fields are **attributes on `project`**.
- A selected label like `story_count` is **not** an attribute on the ORM `Project` instance.
- Therefore: either **construct the schema explicitly** (`ProjectListResponseSchema(..., story_count=...)`) or **validate from a dict** that includes `story_count`.

### SQLAlchemy typing footnote (mypy)

- `result.all()` yields `Row[...]` objects; mypy often treats row unpacking loosely → types can degrade.
- `result.tuples().all()` improves inference, but it returns a **`Sequence[tuple[...]]`**, not necessarily a `list[...]`.
  - Fix: annotate as `Sequence[...]` **or** wrap with `list(...)` if you truly need a list.

## API Architecture: Router vs Service vs Repository

- **Router (FastAPI) = transport boundary**: Accept/return Pydantic schemas, do DI, translate *domain errors → HTTP*. Avoid SQLAlchemy `select/commit` and avoid orchestration. **Recall:** “Could this code run in a CLI/worker unchanged?” If no, it belongs here.
- **Service = use-case/workflow boundary**: Express product intent (“render character and notify”, “create project for user”), enforce invariants/policy, coordinate side-effects, raise *domain* exceptions. Keep it framework-agnostic; prefer primitives or a small command DTO, not request schemas. **Recall:** “What is the smallest API that represents what we’re doing?”
- **Repository = persistence boundary**: Own SQLAlchemy query shapes (`join/count/group_by`), persistence mechanics, and accept an `AsyncSession` created per-request by FastAPI. Never import FastAPI/Pydantic. Prefer explicit params to avoid accidental “mass assignment” when API payloads evolve. **Recall:** “Is this line about *how* we fetch/store data?”
