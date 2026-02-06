# Organism Backend

FastAPI backend powering the Organism platform, with the **Comic Builder** as its primary module.

## Tech Stack

- **Framework:** FastAPI + Uvicorn
- **Database:** PostgreSQL (async via SQLAlchemy + asyncpg), JSONB for state storage
- **LLM:** OpenAI GPT-4o (via `instructor` for structured output)
- **Image Generation:** FAL async client (Nano-Banana, SeedDream models)
- **Real-time:** Socket.IO for WebSocket notifications
- **Migrations:** Alembic

## Project Structure

```
backend/
├── main.py                          # FastAPI app entrypoint
├── core/
│   ├── api/routers.py               # Root router aggregation
│   ├── comic_builder/               # Comic Builder module
│   │   ├── api/                     # REST endpoints
│   │   │   ├── projects.py          # Project CRUD
│   │   │   ├── phases.py           # Generation phase endpoints
│   │   │   └── dependencies.py      # Auth & access guards
│   │   ├── generation/              # LLM & image generation phases
│   │   │   ├── story_generator.py
│   │   │   ├── character_extractor.py
│   │   │   ├── character_renderer.py
│   │   │   ├── panel_generator.py
│   │   │   ├── panel_renderer.py
│   │   │   └── bulk_panel_generator.py
│   │   ├── state/                   # Domain models (Pydantic)
│   │   │   ├── story.py
│   │   │   ├── character.py
│   │   │   ├── panel.py
│   │   │   ├── artifact.py
│   │   │   └── consolidated.py
│   │   ├── models.py                # SQLAlchemy ORM
│   │   ├── schemas.py               # Request/response schemas
│   │   ├── state_manager.py         # State persistence
│   │   ├── asset_manager.py         # Character asset tracking
│   │   └── exceptions.py            # Domain exceptions
│   ├── services/
│   │   └── intelligence/
│   │       ├── clients.py           # OpenAI + instructor clients
│   │       └── media_generator.py   # FAL client with rate limiting
│   └── sockets/                     # Socket.IO integration
└── alembic/                         # Database migrations
```

## Comic Builder Architecture

### Pipeline Overview

The comic builder follows a phased pipeline where each step builds on the output of the previous one:

```
Story → Characters → Panels → Rendered Images
```

### Phase 1: Story Generation

User provides a prompt. GPT-4o generates a story using a hero's journey system prompt. The response is **streamed** as NDJSON (`SimpleEnvelope` format) so the frontend can render text incrementally. The full story is persisted to project state on completion.

**Status lifecycle:** `idle → streaming → completed | error`

### Phase 2: Character Extraction

The story text is fed to GPT-4o via `instructor` (structured output). The LLM identifies characters and returns detailed profiles:

- `name`, `brief`, `character_type` (humanoid / creature / concept / object)
- `era`, `visual_form`, `color_palette`, `distinctive_markers`
- `demeanor`, `role` (protagonist / antagonist / supporting / minor)

Characters are stored in state keyed by UUID.

### Phase 3: Character Rendering

Each character is rendered individually via FAL. Prompts are **type-aware** — humanoids get turnaround sheets, creatures get reference sheets, concepts get symbolic/abstract rendering. This produces a reference image URL stored as an `Artifact` on the character.

### Phase 4: Panel Generation

The story text and a **cast list** (available character names from the AssetManager) are sent to GPT-4o. The LLM breaks the story into panel descriptions, each with:

- `background` — scene description
- `characters` — list of character names (constrained to the cast list)
- `dialogue` — panel text/speech

### Phase 5: Panel Rendering

For each panel, the AssetManager resolves character names → image URLs. If characters are present, an **edit model** composites them into the scene. If no characters are present, a **generation model** creates the scene from text alone. Results are stored as `Artifact` on each panel.

### Phase 6: Bulk Panel Rendering

Renders all panels sequentially, emitting a WebSocket `state.updated` event after each panel so the UI can show progress.

### Key Design Decisions

**JSONB State Storage** — The entire `ConsolidatedComicState` (story + characters + panels) is stored as a single JSONB column on the `Project` model. This keeps the schema simple and allows atomic state updates.

**Asset Manager for Character Consistency** — The `AssetManager` provides slug-normalized name → UUID → URL resolution, ensuring panels reference the correct character images. Missing characters are handled gracefully (logged and skipped).

**Concurrent Media Generation** — The `ConcurrentMediaGenerator` wraps all FAL calls behind an `asyncio.Semaphore(10)` to prevent overwhelming the external API. It also handles **model selection** — choosing between generation and edit models based on whether character image URLs are provided.

**WebSocket Notifications** — Long-running operations (character renders, panel renders) emit Socket.IO events so the frontend can update in real-time without polling.

## API Endpoints

### Projects (`/api/comic-builder/projects`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/projects` | List user projects |
| POST | `/projects` | Create project |
| GET | `/projects/{id}` | Get project with full state |
| PATCH | `/projects/{id}` | Update project state |
| DELETE | `/projects/{id}` | Delete project |

### Generation Phases (`/api/comic-builder/phase`)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate-story/{id}` | Generate story (streaming NDJSON) |
| GET | `/extract-characters/{id}` | Extract characters from story |
| POST | `/render-character/{id}` | Render a single character |
| GET | `/generate-panels/{id}` | Generate panel descriptions |
| POST | `/render-panel/{id}` | Render a single panel |
| POST | `/render-all-panels/{id}` | Batch render all panels |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

## Environment Variables

Requires `OPENAI_API_KEY`, `FAL_KEY`, and database connection config. See `.env.example` for the full list.
