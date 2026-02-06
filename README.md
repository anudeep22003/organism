# StoryEngine Monorepo

This repository contains **StoryEngine**, a creative platform for storytellers.

StoryEngine is a growing set of tools that help artists turn ideas into finished media. We are starting with **comics**, but the system is designed to expand into full multi‑modal generation: illustrated stories, video comics, and eventually motion and film‑like outputs.

The repo is organized as a **monorepo** with a decoupled frontend and backend. Each side has its own detailed README; this document explains how the pieces fit together and where to start.

---

## Vision

StoryEngine treats storytelling as a **directable process**, not a single prompt.

Creators move through clear, inspectable stages where intent, structure, and visual continuity are preserved:

```
Prompt → Story → Characters → Scenes → Images → Media
```

Today, this pipeline is implemented as a **Comic Builder**. Tomorrow, the same foundations power richer formats.

Under the hood, StoryEngine combines:

- LLM-driven structured generation (story, characters, panels)
- Deterministic state management across phases
- Async image generation and compositing
- Real-time progress updates via WebSockets

The frontend and backend are intentionally opinionated and tightly aligned around this philosophy: tools should amplify storytellers, not replace them.

---

## Repository Layout

```
.
├── frontend/        # Web UI (Vite + React)
├── backend/         # API, generation pipeline, persistence (FastAPI)
└── README.md        # You are here
```

- `frontend/README.md` explains the storyteller-facing tool: UI, phases, and creative workflow.
- `backend/README.md` explains the engine: APIs, generation pipeline, data models, and infrastructure.

If you are modifying behavior, read **both** — they are designed to mirror each other conceptually.

---

## System Overview

```
┌────────────┐        REST / Streams        ┌──────────────┐
│            │ ─────────────────────────▶ │              │
│ Frontend   │                             │   Backend    │
│ Story Tool │ ◀──────── WebSockets ────── │ StoryEngine  │
│            │        (state updates)      │              │
└────────────┘                             └──────┬───────┘
                                                         │
                                                         │
                                  ┌──────────────────────┼──────────────────────┐
                                  │                      │                      │
                           ┌────────────┐        ┌────────────┐        ┌────────────┐
                           │   LLMs     │        │ Image Gen  │        │   Storage  │
                           │ (Story,    │        │ (Characters│        │  (State +  │
                           │  Structure)│        │  Panels)   │        │  Assets)   │
                           └────────────┘        └────────────┘        └────────────┘
```

- The frontend is a **director’s console** for the storyteller.
- The backend is the **engine**, coordinating language, images, and state.
- External systems are replaceable; the pipeline and state model are not.

Key properties of the system:

- **Single canonical state** per project (story + characters + panels)
- **Phase-driven workflow** with explicit transitions
- **Idempotent UI** — refresh-safe, no hidden client state

---

## Quick Start (Local Development)

High level only; see the individual READMEs for details.

1. Start the backend
   - Follow setup in `backend/README.md`
   - Ensure required environment variables are set
   - Default server runs on `http://localhost:8080`

2. Start the frontend
   - Follow setup in `frontend/README.md`
   - Point `VITE_BACKEND_URL` at the backend

3. Open the app
   - Visit the frontend dev URL
   - Create a project and walk through the builder

---

## Design Philosophy

- **Tools for artists** — the system assists, it does not author in isolation
- **Phases over magic** — every step is explicit, repeatable, and debuggable
- **State as creative memory** — continuity matters across time and formats
- **Progress, not waiting** — streaming and real‑time feedback are first‑class
- **Consistency enables style** — asset reuse preserves identity

The system favors clarity and debuggability over maximal abstraction.

---

## Where to Go Next

- Exploring the tool as a storyteller: start with `frontend/README.md`
- Extending the engine or adding media types: start with `backend/README.md`
- Building new formats (video, motion, hybrid): add phases without breaking state

This README is intentionally high level. The real documentation lives next door.
