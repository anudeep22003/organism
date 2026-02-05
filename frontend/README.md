# Comic Builder Frontend

This app currently ships a working comic builder flow. The core loop is: create a project, write a story, extract characters, generate panels, render panels, and export as a ZIP.

**Quick start**
1. `npm install`
2. `npm run dev`

**Environment**
1. `VITE_BACKEND_URL` - API + Socket base URL (default `http://localhost:8080`)

**Routing**
1. `/` shows the Projects list.
2. `/:projectId` opens the comic builder for a specific project.

**Project lifecycle**
1. Projects are fetched and created via `src/pages/comic-builder/slices/projectsSlice.ts`.
2. The Projects UI is `src/pages/comic-builder/ProjectsPage.tsx`, with cards in `ProjectCard` and a create dialog in `CreateProjectDialog`.
3. Clicking a project navigates to `/:projectId`.

**Builder workflow (what works today)**
1. The builder UI is `src/pages/comic-builder/components/ComicBuilder.tsx`.
2. A stepper drives phases defined in `src/pages/comic-builder/phaseMap.ts`.
3. Phases are:
4. `write-story` - `WriteStoryPhase` streams story text from the backend.
5. `extract-characters` - `ExtractCharactersPhase` fetches characters from the story.
6. `generate-characters` - `GenerateCharacterPhase` renders images per character.
7. `generate-panels` - `GeneratePanelsPhase` generates comic panels from the story.
8. `render-panels` - `RenderPanelsPhase` renders images per panel, single or bulk.
9. `export-panels` - `ExportPanelsPhase` downloads rendered panels as a ZIP.

**How the data flows**
1. Active project state lives in Redux `comicSlice` (`src/pages/comic-builder/slices/comicSlice.ts`).
2. On page load, `fetchComicState` pulls the project and flattens `state` into the slice.
3. Story generation uses `httpClient.streamPost` to consume newline-delimited JSON and append deltas.
4. Character/panel generation and rendering call phase endpoints and then rely on `state.updated` from Socket.IO to refetch (`useSocket` triggers `fetchComicState`).

**Key APIs used**
1. Project CRUD: `GET/POST /api/comic-builder/projects`
2. Project detail: `GET /api/comic-builder/projects/:id`
3. Story stream: `POST /api/comic-builder/phase/generate-story/:id`
4. Characters: `GET /api/comic-builder/phase/extract-characters/:id`
5. Character render: `POST /api/comic-builder/phase/render-character/:id`
6. Panels: `GET /api/comic-builder/phase/generate-panels/:id`
7. Panel render: `POST /api/comic-builder/phase/render-panel/:id`
8. Bulk render: `POST /api/comic-builder/phase/render-all-panels/:id`

**Export**
1. `ExportPanelsPhase` uses `src/pages/comic-builder/utils.ts` to fetch rendered images and zip them client-side with JSZip.
2. Export only enables once at least one panel has a render URL.

**State + realtime**
1. Redux stores the canonical comic state: `story`, `characters`, and `panels`.
2. The backend emits `state.updated` over Socket.IO, and the frontend refetches the project to stay in sync.

**Where to look first**
1. `src/pages/comic-builder/components/ComicBuilder.tsx` - phase router and stepper.
2. `src/pages/comic-builder/phaseMap.ts` - single source of truth for phases.
3. `src/pages/comic-builder/components/phases/*` - each phase’s UI and action.
4. `src/pages/comic-builder/slices/thunks/*` - API calls for story/characters/panels.
5. `src/pages/comic-builder/slices/comicSlice.ts` - state shape and streaming updates.
