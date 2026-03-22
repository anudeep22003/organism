# Agent Handoff: Organism Codebase

This document grounds you on what exists, what matters, and where to focus. Read this before making changes.

## What Is This Project?

A narrative engine that lets users create projects, write stories (via LLM streaming), and eventually extract characters, generate scenes, and render comic panels. Think of it as a vertical pipeline: Story -> Characters -> Scenes -> Renders.

We are in the 0-1 phase. No users. Only project creation and story generation are implemented and working.

---

## Two Systems Exist — Only One Is Active Development

### V2 (Active — where all new work happens)

- **Frontend:** `frontend/src/features/story/`
- **Backend API:** `backend/core/story_engine/api/v2/`
- **Backend logic:** `backend/core/story_engine/repository.py`, `service.py`, `events.py`
- **URL prefix:** `/api/comic-builder/v2/...`
- **Frontend routes:** `/story`, `/story/p/:projectId`, `/story/p/:projectId/s/:storyId`
- **State management:** TanStack React Query
- **Data model:** Relational tables (project, story). Clean and minimal.

### V1 (Legacy — do not modify unless explicitly asked)

- **Frontend:** `frontend/src/pages/comic-builder/`
- **Backend API:** `backend/core/story_engine/api/projects.py`, `api/phases.py`
- **Backend logic:** `backend/core/story_engine/generation/`, `state_manager.py`, `state/`
- **URL prefix:** `/api/comic-builder/...` (no v2 prefix)
- **Frontend routes:** `/comic`
- **State management:** Redux Toolkit
- **Data model:** Single JSONB blob (`Project.state`) storing a `ConsolidatedComicState` with story, characters, and panels all in one column.

V1 is functional and still routed. It uses a completely different architecture (JSONB state vs relational tables, Redux vs React Query). Do not touch it unless explicitly told to.

---

## Database: What Exists

Only 4 tables exist (after recent cleanup):

| Table | Purpose |
|-------|---------|
| `user` | Auth. Email/password. |
| `session` | Auth sessions (refresh tokens). |
| `project` | Has `user_id`, `name`, `state` (JSONB, used by V1 only), `stories` relationship. |
| `story` | Has `project_id`, `story_text` (Text), `user_input_text` (Text — the latest refine prompt, overwrites each time), `meta` (JSONB). |

Tables for character, scene, story_character, scene_character, and render_job were removed. They were premature. We will reintroduce them one at a time as needed through vertical slices.

**ORM:** SQLAlchemy async with `asyncpg`. Models at `backend/core/story_engine/models/`.
**Migrations:** Alembic at `backend/alembic/`.
**Schemas:** Pydantic with camelCase aliasing via `AliasedBaseModel`. At `backend/core/story_engine/schemas/`.

---

## V2 Backend Architecture

### Models (`backend/core/story_engine/models/`)

- `Project` — owns many `Story` via `stories` relationship (cascade delete-orphan). Has a `state` JSONB column used only by V1.
- `Story` — belongs to `Project`. Stores `story_text` and `user_input_text` (single string, the latest prompt).

### Schemas (`backend/core/story_engine/schemas/`)

| Schema | Used By |
|--------|---------|
| `ProjectCreateSchema` | V1 + V2 create project |
| `ProjectUpdateSchema` | V1 only (updates JSONB state) |
| `ProjectResponseSchema` | V1 + V2 project response |
| `ProjectListResponseSchema` | V2 project listing (includes `story_count`) |
| `ProjectRelationalStateSchema` | V2 project detail (extends response with `stories` list) |
| `StoryCreateSchema` | V2 create story |
| `StoryResponseSchema` | V2 story response |
| `GenerateStoryRequest` | V2 story generation (has `story_prompt` field) |

### Repository (`backend/core/story_engine/repository.py`)

Data access layer for V2. All queries go through here:
- `get_all_projects_of_user_with_story_count()` — list projects with story count via outerjoin
- `create_project()` / `create_new_story()` — basic creation
- `get_project_details()` — loads project with `selectinload(Project.stories)`
- `get_story()` / `delete_story()` — basic CRUD
- `get_story_with_project()` — used for ownership checks, uses `joinedload(Story.project)`
- `update_story_with_story_and_prompt()` — overwrites `story_text` and `user_input_text` after generation completes

### Service (`backend/core/story_engine/service.py`)

Orchestrates story generation:
1. Validates user owns the story (via `_check_story_ownership`)
2. Streams from OpenAI (`StoryStreamGenerator`)
3. Processes chunks into `EventEnvelope` events (`OpenAIStreamProcessor`)
4. Accumulates full text, persists on `stream.end` via repository
5. Yields errors as `stream.error` events if anything fails

### Events (`backend/core/story_engine/events.py`)

V2 streaming uses NDJSON over HTTP (not WebSocket). The `EventEnvelope` schema:
- `event_type`: `stream.start`, `stream.chunk`, `stream.end`, `stream.error`
- `payload`: `{ delta }` for start/chunk, `{ finish_reason }` for end
- `error`: `{ code, message, retryable }` for errors

### API Routes (`backend/core/story_engine/api/v2/`)

| Method | Path | Handler |
|--------|------|---------|
| GET | `/v2/projects` | List projects with story count |
| POST | `/v2/projects` | Create project |
| GET | `/v2/projects/{project_id}` | Get project with stories |
| POST | `/v2/projects/{project_id}/story` | Create story in project |
| DELETE | `/v2/projects/{project_id}/story/{story_id}` | Delete story |
| GET | `/v2/project/{project_id}/story/{story_id}` | Get single story |
| POST | `/v2/story/{story_id}/generate` | Stream-generate story (NDJSON) |

All V2 routes are under the `/api/comic-builder/v2` prefix (see `api/routers.py`).

---

## V2 Frontend Architecture

### Location: `frontend/src/features/story/`

```
features/story/
  index.tsx              # barrel export
  routes.tsx             # /story routes (ProjectList, ProjectHome, StoryWorkspace)
  components/
    ArtifactCard/        # reusable card with refine input, collapse, stale badge
    StoryContent.tsx     # renders story text with streaming cursor
  events/
    baseEvents.ts        # EventEnvelope type definitions
    eventRouter.ts       # routes stream events into React Query cache
  Projects/
    ProjectList.tsx      # /story — lists all projects, create form
    ProjectHome.tsx      # /story/p/:id — shows project with its stories
    types.ts             # ProjectListEntryType, StoryListEntryType, etc.
    components/          # ProjectCard, StoryCard
    hooks/               # useProjectList, useProjectHome, useCreateProject, useAddStory, useDeleteStory
  StoryPhase/
    StoryWorkspace.tsx   # /story/p/:id/s/:id — story editing with ArtifactCard
    types.ts             # StoryDetailType, StoryStreamChunk
    hooks/
      useStoryPhase.ts   # orchestrates story detail + stream generation
      useStoryDetail.ts  # GET story detail via React Query
      useStoryStream.ts  # POST story generation, streams NDJSON, routes events to cache
```

### Key Patterns

**Data fetching:** TanStack React Query with `queryOptions` pattern. Query keys are defined next to hooks (e.g., `storyDetailKeys` in `useStoryDetail.ts`).

**Streaming:** `useStoryStream` uses `httpClient.streamPost()` to consume NDJSON. Each event is routed through `EventRouter` which updates the React Query cache directly via `queryClient.setQueryData`. This gives real-time streaming updates without extra state.

**HTTP Client:** Singleton `httpClient` at `frontend/src/lib/httpClient.ts`. Wraps Axios for regular requests and `fetch` for streaming. Handles auth token injection and automatic 401 refresh.

**ArtifactCard:** The core reusable component. Renders any content with:
- Title header
- Collapsible content (overflow detection, gradient fade)
- Stale badge (wired but not yet used — no invalidation system yet)
- Refine input (text + optional file attachments)
- Loading skeleton

Currently only used for Story in `StoryWorkspace.tsx`. Will be reused for Characters and Scenes when those are built.

### What StoryWorkspace Looks Like Right Now

```
[Back to project link]
[ArtifactCard: Story]
  - Shows story text (or placeholder if empty)
  - Refine button opens input to submit a prompt
  - Prompt streams story from LLM, text appears in real-time
[PlaceholderSection: Characters — coming soon]
[PlaceholderSection: Scenes — coming soon]
```

---

## Auth System

Fully implemented and working. JWT access tokens + httpOnly refresh cookie.

- **Backend:** `backend/core/auth/` — User model, AuthSession model, managers for password/JWT/session/refresh
- **Frontend:** `frontend/src/features/auth/` — AuthPage, SignIn/SignUp forms, RequireAuth/RequireGuest guards, token store

Do not modify auth unless explicitly asked.

---

## Other Systems (Exist But Not Active Focus)

- **WebSocket / Socket.IO:** `backend/core/sockets/`, `frontend/src/socket/` — multi-agent chat system. Used by the HumanAiWorkspace page at `/generative-space`. Separate from story engine.
- **Agent system:** `backend/agents/` — LLM task orchestration via timeline events. Connected to sockets.
- **Audio/transcription:** `frontend/src/audio/`, backend endpoint at `/api/transcribe/whisper`.
- **V1 generation pipeline:** `backend/core/story_engine/generation/` — StoryPhase, CharacterExtractor, CharacterRenderer, PanelGenerator, PanelRenderer. All operate on JSONB state. Do not touch.

---

## Tech Stack

### Backend
- Python 3.12, FastAPI, SQLAlchemy async, Alembic
- PostgreSQL with asyncpg
- OpenAI SDK for LLM calls
- uv for package management
- Ruff for formatting/linting, mypy for type checking

### Frontend
- React 19, TypeScript, Vite
- TanStack React Query (data fetching)
- React Router v7
- Tailwind CSS + shadcn/ui components
- Tabler Icons
- bun for package management
- ESLint for linting

---

## Coding Principles

- Do not repeat yourself
- Premature optimization is the root of all evil
- Introduce the minimum number of changes to achieve the desired task
- Code should be self-documenting, no comments unless necessary
- All names should be descriptive and meaningful and read like elegant prose in the stacktrace
- Use the most specific type possible, avoid `Any`
- Files should not be longer than 200 lines of code
- Always vertical slices — never build schema without UI, or UI without backend

To verify backend, run `make check` in the backend directory.
To verify frontend, run `tsc -b --noEmit` or `npm run type-check` equivalently in the frontend directory.