# Story Feature — Architecture Guide

This document is the entry point for any agent or developer working on the story feature. Read it before touching anything.

---

## Directory Structure

```
src/features/story/
├── shared/                        # Cross-cutting concerns used by 2+ modules
│   ├── story.constants.ts         # STORY_API_BASE, STORY_QUERY_ROOT
│   └── story.types.ts             # Domain types shared across phases and projects
├── events/
│   ├── base-events.ts             # EventEnvelope and stream event type definitions
│   └── event-router.ts            # Handles NDJSON stream events, patches query cache
├── phases/                        # One subdirectory per pipeline phase
│   └── story-phase/               # Story text generation phase
│       ├── story-phase.queries.ts # queryOptions factories for this phase
│       ├── story-phase.types.ts   # Types scoped to this phase only
│       ├── hooks/
│       │   ├── useStoryPhase.ts   # Composed hook consumed by StoryWorkspace
│       │   └── useStoryStream.ts  # Mutation: streams generation, patches cache
│       └── ui/
│           └── StoryWorkspace.tsx # Route-level component for this phase
├── projects/                      # Project and story list management
│   ├── projects.queries.ts        # queryOptions factories for projects layer
│   ├── projects.types.ts          # Types scoped to projects only
│   ├── hooks/
│   │   ├── useAddStory.ts
│   │   ├── useCreateProject.ts
│   │   └── useDeleteStory.ts
│   └── ui/
│       ├── ProjectHome.tsx
│       ├── ProjectList.tsx
│       └── components/
│           ├── ProjectCard.tsx
│           └── StoryCard.tsx
├── components/                    # Shared UI used across multiple phases
│   ├── ArtifactCard/              # The primary phase output card with refine input
│   ├── ContentCard.tsx
│   ├── HistoryCard.tsx
│   ├── HistoryOverlay.tsx
│   └── StoryContent.tsx
├── routes.tsx                     # React Router route definitions for the feature
└── index.tsx                      # Public barrel — only export what leaves this feature
```

---

## Core Patterns

### 1. queryOptions factories (not custom hooks)

Every query is defined as an exported `queryOptions` factory in a `*.queries.ts` file. The factory co-locates the query key and query function.

```ts
// phases/story-phase/story-phase.queries.ts
export const storyDetailOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [...STORY_QUERY_ROOT, "project", projectId, "story", storyId],
    queryFn: () => httpClient.get<StoryDetailType>(`${STORY_API_BASE}/...`),
    enabled: !!projectId && !!storyId,
  })
```

Consume directly in components or hooks — no wrapping custom hook unless it adds real logic:

```ts
const { data } = useQuery(storyDetailOptions(projectId, storyId))
```

Use `.queryKey` for invalidation from mutations:

```ts
queryClient.invalidateQueries({
  queryKey: storyDetailOptions(projectId, storyId).queryKey,
})
```

### 2. Query key hierarchy

All keys start with `STORY_QUERY_ROOT = ["story"]`. Keys are structured from broad to specific so fuzzy prefix matching works for bulk invalidation.

```
["story"]                                               — everything in the feature
["story", "projects"]                                   — all projects
["story", "projects", projectId]                        — one project + its stories
["story", "project", projectId, "story", storyId]       — one story's detail
["story", "project", projectId, "story", storyId, "history"]
["story", "project", projectId, "story", storyId, "characters"]   (future)
["story", "project", projectId, "story", storyId, "panels"]       (future)
```

New phases must follow this hierarchy. Register all keys in the phase's own `*.queries.ts` file.

### 3. Shared vs. phase-scoped

Put something in `shared/` only when two or more modules already need it.

| Put in `shared/` | Put in the phase |
|---|---|
| Types referenced across phases | Types only one phase uses |
| `STORY_API_BASE` constant | Phase-specific endpoint paths |
| `STORY_QUERY_ROOT` | Phase-specific query keys |

### 4. Streaming (EventRouter)

The generation endpoints return NDJSON streams with typed `EventEnvelope` messages (`stream.start`, `stream.chunk`, `stream.end`, `stream.error`). `EventRouter` receives these events and patches the query cache via `setQueryData` so the UI updates in real time without a refetch.

`EventRouter` is currently hardcoded to `StoryDetailType`. When a future phase has its own streaming endpoint that needs real-time cache patching, make `EventRouter` generic. If the phase only needs a loading indicator (spinner while generating), skip `EventRouter` entirely — just use `useMutation` with `isPending` and invalidate on `onSuccess`.

### 5. Thin hooks are not a pattern here

Do not create a custom hook that only wraps `useQuery(someOptions(...))`. Call `useQuery` inline at the usage site. Custom hooks are only justified when they compose multiple queries, mutations, or side effects into a single interface (see `useStoryPhase` as the model).

---

## Adding a New Phase

Follow these steps in order. Each step should leave the build passing.

### Step 1 — Create the phase directory

```
phases/<phase-name>/
├── <phase-name>.queries.ts
├── <phase-name>.types.ts
├── hooks/
│   └── use<PhaseName>.ts        # composed hook, if needed
└── ui/
    └── <PhaseName>Workspace.tsx # route-level component
```

### Step 2 — Define types

In `<phase-name>.types.ts`, define only types that belong exclusively to this phase. If a type is needed by another phase or by the projects layer, put it in `shared/story.types.ts`.

### Step 3 — Define query options

In `<phase-name>.queries.ts`:

```ts
import { STORY_API_BASE, STORY_QUERY_ROOT } from "../../shared/story.constants"

export const <phaseName>Options = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project", projectId,
      "story", storyId,
      "<phase-segment>",  // e.g. "characters", "panels"
    ] as const,
    queryFn: () => httpClient.get<PhaseType>(`${STORY_API_BASE}/...`),
    enabled: !!projectId && !!storyId,
  })
```

### Step 4 — Define mutations (if the phase has a generate/render action)

Add mutation hooks to `hooks/`. Each mutation invalidates via `.queryKey` from the queries file:

```ts
import { <phaseName>Options } from "../<phase-name>.queries"

onSuccess: () =>
  queryClient.invalidateQueries({
    queryKey: <phaseName>Options(projectId, storyId).queryKey,
  })
```

If the mutation streams NDJSON and needs real-time cache patching, use `EventRouter`. If it just needs a loading state, use `isPending` from `useMutation` and invalidate on `onSuccess`.

### Step 5 — Build the UI component

In `ui/<PhaseName>Workspace.tsx`, consume queries directly:

```ts
const { data } = useQuery(<phaseName>Options(projectId, storyId))
```

Use `ArtifactCard` from `../../components/ArtifactCard` as the container — it provides the standard card chrome, refine input, collapse behaviour, and history button slot.

### Step 6 — Add the route

In `routes.tsx`, add the new route and import from the new ui path. The existing route pattern:

```ts
{
  path: `${ROOT_PATH}/p/:projectId/s/:storyId`,
  element: <StoryWorkspace />,
}
```

Phase workspaces currently render as sections inside `StoryWorkspace` rather than separate routes. Add your `<PlaceholderSection>` replacement there.

### Step 7 — Verify

```
npm run type-check
npm run lint
```

Both must pass with zero errors before committing.

---

## Backend API Base

All v2 endpoints are under `/api/comic-builder/v2` (`STORY_API_BASE`). The full route table is documented in the backend at `backend/core/story_engine/api/v2/`. Key routes for phases:

```
GET  /project/:projectId/story/:storyId                         — story detail
POST /project/:projectId/story/:storyId/generate                — stream story
GET  /project/:projectId/story/:storyId/history                 — edit events

GET  /project/:projectId/story/:storyId/characters              — character list
POST /project/:projectId/story/:storyId/characters              — extract from story
GET  /project/:projectId/story/:storyId/character/:characterId
POST /project/:projectId/story/:storyId/character/:characterId/render

GET  /project/:projectId/story/:storyId/panels                  — panel list
POST /project/:projectId/story/:storyId/panels/generate         — bulk generate
GET  /project/:projectId/story/:storyId/panel/:panelId
POST /project/:projectId/story/:storyId/panel/:panelId/render

GET  /image/:imageId/signed-url
```

All responses use camelCase keys (pydantic `AliasedBaseModel`).
