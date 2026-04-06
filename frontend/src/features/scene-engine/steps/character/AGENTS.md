# Character Step Refactor — Handoff Document

## Context

The `character-extraction` and `character-rendering` steps under `scene-engine/steps/` were built separately and share significant duplicated logic. This document describes the agreed refactor to consolidate shared character-domain concerns and eliminate all duplication before the panel steps are built (which will follow the exact same pattern).

The owner has reviewed and approved every decision below. Do not re-litigate them — execute the plan.

---

## Current structure (what exists today)

```
scene-engine/steps/
├── character-extraction/
│   ├── character-extraction.queries.ts
│   ├── character-extraction.types.ts
│   ├── CharacterAttributes.tsx
│   ├── CharacterExtractionStep.tsx
│   ├── components/
│   │   ├── CharacterCard.tsx
│   │   ├── CharacterList.tsx
│   │   ├── CharacterModal.tsx
│   │   ├── ReferenceImageViewer.tsx
│   │   └── RefImageTray.tsx
│   └── hooks/
│       └── useCharacterExtraction.ts
└── character-rendering/
    ├── character-rendering.queries.ts
    ├── character-rendering.types.ts     ← only re-exports ImageRecord as RenderRecord
    ├── CharacterRenderingStep.tsx
    ├── components/
    │   ├── Carousel.tsx
    │   ├── CharacterRenderingList.tsx
    │   ├── CharacterRenderList.tsx      ← dead file, returns null
    │   ├── CharacterRenderModal.tsx
    │   └── EmptyState.tsx
    └── hooks/
        └── useCharacterRendering.ts
```

The step registry is at `scene-engine/steps.ts` and currently imports:
```ts
import CharacterExtractionStep from "./steps/character-extraction/CharacterExtractionStep";
import CharacterRenderingStep from "./steps/character-rendering/CharacterRenderingStep";
```

---

## Target structure (what to build)

```
scene-engine/steps/
└── character/
    ├── character.types.ts
    ├── character.queries.ts
    ├── character.utils.ts
    ├── extraction/
    │   ├── hooks/
    │   │   └── useCharacterExtraction.ts
    │   ├── components/
    │   │   ├── CharacterAttributes.tsx
    │   │   ├── CharacterCard.tsx
    │   │   ├── CharacterList.tsx
    │   │   ├── CharacterModal.tsx
    │   │   ├── ReferenceImageViewer.tsx
    │   │   └── RefImageTray.tsx
    │   └── CharacterExtractionStep.tsx
    └── rendering/
        ├── rendering.queries.ts
        ├── hooks/
        │   └── useCharacterRendering.ts
        ├── components/
        │   ├── Carousel.tsx
        │   ├── CharacterRenderingList.tsx
        │   ├── CharacterRenderModal.tsx
        │   └── EmptyState.tsx
        └── CharacterRenderingStep.tsx
```

Note: `extraction.queries.ts` does NOT exist in the target — after moving shared queries up, extraction has no queries of its own. Do not create an empty placeholder.

---

## All decisions taken

### 1. STORY_API_BASE — import from shared
Both `useCharacterExtraction.ts` and `useCharacterRendering.ts` declare their own:
```ts
const STORY_API_BASE = "/api/comic-builder/v2" as const;
```
**Decision:** Delete both local declarations. Import from `@/features/story/shared/story.constants`.

### 2. STORY_QUERY_ROOT — import from shared
`character-extraction.queries.ts` declares its own local `STORY_QUERY_ROOT`. `character-rendering.queries.ts` hardcodes `"story"` directly in the key array.
**Decision:** Both import `STORY_QUERY_ROOT` from `@/features/story/shared/story.constants`.

### 3. ImageRecord — promote to story shared types
`ImageRecord` is a general image shape used across character extraction, character rendering, and will be used by panel steps. It currently lives only in `character-extraction.types.ts`.
**Decision:** Add `ImageRecord` to `@/features/story/shared/story.types.ts`. All imports of `ImageRecord` point there.

```ts
// Add to frontend/src/features/story/shared/story.types.ts
export type ImageRecord = {
  id: string;
  objectKey: string;
  bucket: string;
  contentType: string;
  width: number;
  height: number;
  sizeBytes: number;
  createdAt: string;
};
```

### 4. RenderRecord — deleted entirely
`character-rendering.types.ts` only contains:
```ts
import type { ImageRecord } from "../character-extraction/character-extraction.types";
export type RenderRecord = ImageRecord;
```
**Decision:** `RenderRecord` is deleted. `character-rendering.types.ts` is deleted. All usages of `RenderRecord` in the rendering step switch to `ImageRecord` imported from `@/features/story/shared/story.types`.

### 5. CharacterRecord, CharacterBundle — move to character domain
These types are used by both steps but currently live in `character-extraction.types.ts`, creating a hard dependency from rendering → extraction.
**Decision:** Move to `character/character.types.ts`. Import `ImageRecord` from `@/features/story/shared/story.types`.

```ts
// character/character.types.ts
import type { ImageRecord } from "@/features/story/shared/story.types";

export type CharacterRecord = {
  id: string;
  name: string;
  slug: string;
  attributes: Record<string, unknown>;
  meta: Record<string, unknown>;
  sourceEventId: string | null;
  createdAt: string;
  updatedAt: string;
};

export type CharacterBundle = {
  character: CharacterRecord;
  canonicalRender: ImageRecord | null;
  referenceImages: ImageRecord[];
};
```

### 6. charactersOptions — move to character domain
Currently in `character-extraction.queries.ts` but consumed by both steps. `CharacterRenderingStep.tsx` and `useCharacterRendering.ts` import it from the extraction folder, creating a cross-step dependency.
**Decision:** Move to `character/character.queries.ts`. Both steps import from there.

### 7. imageSignedUrlOptions — move to character domain
Currently in `character-extraction.queries.ts` but consumed by 4 files across both steps:
- `ReferenceImageViewer.tsx` (extraction)
- `RefImageTray.tsx` (extraction)
- `Carousel.tsx` (rendering)
- `CharacterRenderingList.tsx` (rendering)

The query has no character-specific logic — it fetches a signed URL for any image ID.
**Decision:** Move to `character/character.queries.ts`.

**Important note for panel agent:** When panel steps are built, they will also need `imageSignedUrlOptions`. At that point, promote it from `character/character.queries.ts` up to `@/features/story/shared/` so both character and panel domains can share it. Do not duplicate it.

### 8. spliceCharacterIntoList — move to character.utils.ts
Currently only in `useCharacterExtraction.ts` as a local function. `useCharacterRendering.ts` duplicates the same logic inline.
**Decision:** Move to `character/character.utils.ts`. Both hooks import and use it.

```ts
// character/character.utils.ts
import type { CharacterBundle } from "./character.types";

export function spliceCharacterIntoList(
  list: CharacterBundle[],
  updated: CharacterBundle,
): CharacterBundle[] {
  return list.map((b) =>
    b.character.id === updated.character.id ? updated : b,
  );
}
```

### 9. uploadReferenceImage — unified mutation fn, upgraded onSuccess in rendering
The `mutationFn` is identical in both hooks. The rendering hook's `onSuccess` was a blunt `invalidateQueries` kept for simplicity — the right approach is the extraction hook's surgical `setQueryData` + `spliceCharacterIntoList`.

**Decision:** Extract the HTTP call to `character.utils.ts`:
```ts
export async function uploadReferenceImageRequest(
  projectId: string,
  storyId: string,
  characterId: string,
  file: File,
): Promise<CharacterBundle> {
  const formData = new FormData();
  formData.append("image", file);
  return httpClient.post<CharacterBundle>(
    `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/upload-reference-image`,
    formData,
  );
}
```

Both hooks call `uploadReferenceImageRequest` in their `mutationFn`. Each hook keeps its own `useMutation` wrapper with its own `isPending` state. The rendering hook's `onSuccess` is upgraded to:
```ts
onSuccess: (updated) => {
  queryClient.setQueryData(charactersQueryKey, (prev: CharacterBundle[] | undefined) =>
    prev ? spliceCharacterIntoList(prev, updated) : [updated],
  );
},
```

### 10. buildHttpErrorMessage — shared utility
Both hooks have a local function mapping HTTP status codes to user-facing strings. The structure is identical, the status codes differ.
**Decision:** Add to `character/character.utils.ts`:
```ts
export function buildHttpErrorMessage(
  error: unknown,
  statusMessages: Record<number, string>,
  fallback: string,
): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status && statusMessages[status]) return statusMessages[status];
  }
  return fallback;
}
```

`useCharacterExtraction.ts` usage:
```ts
buildHttpErrorMessage(error, {
  400: "Your story has no text yet. Go to Step 1 and write a story first.",
  404: "Story not found. Make sure a story has been created.",
}, "Something went wrong. Try again.")
```

`useCharacterRendering.ts` usage:
```ts
buildHttpErrorMessage(error, {
  401: "Session expired. Please sign in again.",
  404: "Character not found. Try refreshing.",
}, "Render failed. Try again.")
```

### 11. StepLoadingSkeleton — shared component
Both step roots have identical loading states:
```tsx
<div className="flex h-full w-full flex-col gap-2 p-4">
  <Skeleton className="min-h-0 flex-1 w-full" />
  <Skeleton className="min-h-0 flex-1 w-full" />
  <Skeleton className="min-h-0 flex-1 w-full" />
</div>
```
**Decision:** Extract to `scene-engine/components/StepLoadingSkeleton.tsx`. Both step roots import it.

```tsx
// scene-engine/components/StepLoadingSkeleton.tsx
import { Skeleton } from "./Skeleton";

export function StepLoadingSkeleton() {
  return (
    <div className="flex h-full w-full flex-col gap-2 p-4">
      <Skeleton className="min-h-0 flex-1 w-full" />
      <Skeleton className="min-h-0 flex-1 w-full" />
      <Skeleton className="min-h-0 flex-1 w-full" />
    </div>
  );
}
```

### 12. CharacterRenderList.tsx — deleted
Returns null, has no consumers.

### 13. steps.ts — import paths update
```ts
// before
import CharacterExtractionStep from "./steps/character-extraction/CharacterExtractionStep";
import CharacterRenderingStep from "./steps/character-rendering/CharacterRenderingStep";

// after
import CharacterExtractionStep from "./steps/character/extraction/CharacterExtractionStep";
import CharacterRenderingStep from "./steps/character/rendering/CharacterRenderingStep";
```

---

## Execution order

Follow this order exactly. Each step must leave the build passing before proceeding. Run `npm run type-check` after each step. Commit at each checkpoint.

### Step 1 — Add ImageRecord to story shared types
Edit `frontend/src/features/story/shared/story.types.ts` — add `ImageRecord` type (definition in decision #3 above). Commit.

### Step 2 — Create character domain files
Create these three new files with the content defined in the decisions above:
- `scene-engine/steps/character/character.types.ts`
- `scene-engine/steps/character/character.queries.ts`
- `scene-engine/steps/character/character.utils.ts`

`character.queries.ts` full content:
```ts
import { httpClient } from "@/lib/httpClient";
import { queryOptions } from "@tanstack/react-query";
import { STORY_API_BASE, STORY_QUERY_ROOT } from "@/features/story/shared/story.constants";
import type { CharacterBundle } from "./character.types";

export const charactersOptions = (projectId: string, storyId: string) =>
  queryOptions({
    queryKey: [
      ...STORY_QUERY_ROOT,
      "project", projectId,
      "story", storyId,
      "characters",
    ] as const,
    queryFn: () =>
      httpClient.get<CharacterBundle[]>(
        `${STORY_API_BASE}/project/${projectId}/story/${storyId}/characters`,
      ),
    enabled: !!projectId && !!storyId,
    staleTime: Infinity,
  });

export const imageSignedUrlOptions = (imageId: string) =>
  queryOptions({
    queryKey: ["image", imageId, "signed-url"] as const,
    queryFn: () =>
      httpClient.get<{ url: string; expiresAt: string }>(
        `${STORY_API_BASE}/image/${imageId}/signed-url`,
      ),
    enabled: !!imageId,
    staleTime: 55 * 60 * 1000,
  });
```

`character.utils.ts` full content:
```ts
import { isAxiosError } from "axios";
import { httpClient } from "@/lib/httpClient";
import { STORY_API_BASE } from "@/features/story/shared/story.constants";
import type { CharacterBundle } from "./character.types";

export function spliceCharacterIntoList(
  list: CharacterBundle[],
  updated: CharacterBundle,
): CharacterBundle[] {
  return list.map((b) =>
    b.character.id === updated.character.id ? updated : b,
  );
}

export function buildHttpErrorMessage(
  error: unknown,
  statusMessages: Record<number, string>,
  fallback: string,
): string {
  if (isAxiosError(error)) {
    const status = error.response?.status;
    if (status && statusMessages[status]) return statusMessages[status];
  }
  return fallback;
}

export async function uploadReferenceImageRequest(
  projectId: string,
  storyId: string,
  characterId: string,
  file: File,
): Promise<CharacterBundle> {
  const formData = new FormData();
  formData.append("image", file);
  return httpClient.post<CharacterBundle>(
    `${STORY_API_BASE}/project/${projectId}/story/${storyId}/character/${characterId}/upload-reference-image`,
    formData,
  );
}
```

Type-check. Commit: "feat(scene-engine): add character domain types, queries, and utils"

### Step 3 — Create StepLoadingSkeleton
Create `scene-engine/components/StepLoadingSkeleton.tsx` (content in decision #11 above).
Type-check. Commit: "feat(scene-engine): add shared StepLoadingSkeleton component"

### Step 4 — Create extraction/ subdirectory and move files
Create `scene-engine/steps/character/extraction/` with `hooks/` and `components/` subdirs.

Move (copy with updated imports) each file from `character-extraction/` to `character/extraction/`:

**Import changes required in extraction files:**
- All files: `../character-extraction.types` → `../character.types` (one level up, then character.types) — wait, paths: these files move from `character-extraction/X` to `character/extraction/X`, so relative to `character/extraction/`, the character domain files are at `../character.types`, `../character.queries`, `../character.utils`.
- `CharacterExtractionStep.tsx`: replace loading skeleton with `<StepLoadingSkeleton />` from `../../../components/StepLoadingSkeleton`
- `useCharacterExtraction.ts`:
  - Import `STORY_API_BASE` from `@/features/story/shared/story.constants`
  - Import `charactersOptions` from `../../character.queries`
  - Import `CharacterBundle` from `../../character.types`
  - Import `spliceCharacterIntoList`, `uploadReferenceImageRequest`, `buildHttpErrorMessage` from `../../character.utils`
  - Remove local `STORY_API_BASE` declaration
  - Remove local `spliceCharacterIntoList` function
  - Replace `uploadReferenceImage` mutationFn body with call to `uploadReferenceImageRequest`
  - Replace `extractionErrorMessage` function with `buildHttpErrorMessage` call
- `RefImageTray.tsx` and `ReferenceImageViewer.tsx`: import `imageSignedUrlOptions` from `../../character.queries`, import `ImageRecord` from `@/features/story/shared/story.types`

Do NOT delete `character-extraction/` yet.
Type-check. Commit: "feat(scene-engine): add character/extraction with updated imports"

### Step 5 — Create rendering/ subdirectory and move files
Create `scene-engine/steps/character/rendering/` with `hooks/`, `components/` subdirs.

Move each file from `character-rendering/` to `character/rendering/`:

**Import changes required in rendering files:**
- `CharacterRenderingStep.tsx`:
  - Import `charactersOptions` from `../character.queries`
  - Import `CharacterBundle` from `../character.types`
  - Replace loading skeleton with `<StepLoadingSkeleton />` from `../../../components/StepLoadingSkeleton`
- `rendering.queries.ts` (renamed from `character-rendering.queries.ts`):
  - Import `STORY_API_BASE`, `STORY_QUERY_ROOT` from `@/features/story/shared/story.constants`
  - Import `ImageRecord` from `@/features/story/shared/story.types`
  - Remove `RenderRecord` type — use `ImageRecord` directly
  - Return type of `characterRendersOptions` changes from `RenderRecord[]` to `ImageRecord[]`
- `useCharacterRendering.ts`:
  - Import `STORY_API_BASE` from `@/features/story/shared/story.constants`
  - Import `charactersOptions` from `../../character.queries`
  - Import `characterRendersOptions` from `../rendering.queries`
  - Import `CharacterBundle` from `../../character.types`
  - Import `ImageRecord` from `@/features/story/shared/story.types`
  - Import `spliceCharacterIntoList`, `uploadReferenceImageRequest`, `buildHttpErrorMessage` from `../../character.utils`
  - Remove local `STORY_API_BASE` declaration
  - Replace `uploadReferenceImage` mutationFn with call to `uploadReferenceImageRequest`
  - Upgrade `uploadReferenceImage` onSuccess to surgical `setQueryData` + `spliceCharacterIntoList` (matching extraction pattern)
  - Replace `renderErrorMessage` function with `buildHttpErrorMessage` call
  - Replace all `RenderRecord` type references with `ImageRecord`
- `Carousel.tsx`:
  - Import `imageSignedUrlOptions` from `../../character.queries`
  - Import `ImageRecord` from `@/features/story/shared/story.types`
  - Replace `RenderRecord` with `ImageRecord`
- `CharacterRenderingList.tsx`:
  - Import `imageSignedUrlOptions` from `../../character.queries`
  - Import `CharacterBundle`, `ImageRecord` (was `ImageRecord`) from appropriate places
  - Replace `RenderRecord` with `ImageRecord`
- `CharacterRenderModal.tsx`:
  - Import `CharacterBundle` from `../../character.types`
  - Import `ImageRecord` from `@/features/story/shared/story.types`
  - Replace `RenderRecord` with `ImageRecord`
- `EmptyState.tsx`: no import changes needed

Do NOT create `CharacterRenderList.tsx` — it is deleted.
Do NOT delete `character-rendering/` yet.
Type-check. Commit: "feat(scene-engine): add character/rendering with updated imports"

### Step 6 — Update steps.ts
Update import paths in `scene-engine/steps.ts` (changes in decision #13 above).
Type-check. Commit: "refactor(scene-engine): update step registry to character/ paths"

### Step 7 — Delete old directories
```bash
git rm -rf frontend/src/features/scene-engine/steps/character-extraction/
git rm -rf frontend/src/features/scene-engine/steps/character-rendering/
```
Type-check. If casing issues arise (macOS case-insensitive filesystem), follow the same two-step rename approach used in the story refactor: `mv character-extraction character-extraction-tmp && mv character-extraction-tmp` to a new name that doesn't conflict, then delete.
Commit: "refactor(scene-engine): remove old character-extraction and character-rendering directories"

### Step 8 — Update AGENTS.md
Update `scene-engine/AGENTS.md` (if it exists) or create it to document:
- The new `character/` domain structure
- The `imageSignedUrlOptions` note: when panel steps arrive, promote this from `character/character.queries.ts` to `@/features/story/shared/` so panels can share it without duplicating
- The pattern established here is the template for panel steps

Full build verify: `npm run type-check && npm run lint`. Commit: "docs(scene-engine): update AGENTS.md with character domain structure"

---

## Key files to read before starting

Read these before writing a single line of code:
1. `frontend/src/features/story/shared/story.constants.ts` — verify STORY_API_BASE and STORY_QUERY_ROOT exist
2. `frontend/src/features/story/shared/story.types.ts` — verify ImageRecord is not already there
3. `frontend/src/features/scene-engine/steps/character-extraction/hooks/useCharacterExtraction.ts` — source of truth for extraction hook
4. `frontend/src/features/scene-engine/steps/character-rendering/hooks/useCharacterRendering.ts` — source of truth for rendering hook
5. `frontend/src/features/scene-engine/steps.ts` — the step registry

---

## What does NOT change

- All UI component JSX is unchanged — this is purely a restructure + import fix
- `ModalShell`, `PromptInput`, `ValidationErrorBlock`, `Skeleton` stay in `scene-engine/components/`
- `CharacterAttributes.tsx` stays in `extraction/components/` — only used there
- `RefImageTray` and `ReferenceImageViewer` stay in `extraction/components/` — rendering has its own image display (Carousel)
- No business logic changes except upgrading rendering's `uploadReferenceImage` onSuccess to use `setQueryData` instead of `invalidateQueries`
- The `SCENE_STEPS` array in `steps.ts` is unchanged — only the import paths change
