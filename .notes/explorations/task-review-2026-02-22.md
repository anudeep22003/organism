# Task Review: story/.tasks analysis

Date: 2026-02-22

## Does the backend need changes?

No. The v2 backend already supports everything these 4 tasks need.

- `POST /v2/projects/{project_id}/story` returns `StoryResponseSchema` (id, project_id, story_text, etc.) — the frontend just isn't typing the response properly. That's a frontend fix, not a backend gap.
- Route path changes (task 02) are purely frontend routing. The API URLs don't change.
- Query key cleanup (task 03) is entirely client-side cache management.
- Folder reorganization (task 04) is file moves and import rewiring.

One minor backend observation: `create_story` and `delete_story` in `v2/projects.py` have `# TODO verify user_id project ownership` comments — they skip ownership checks. This is a real gap but it's orthogonal to these 4 tasks and would be a distraction to fix now. Note it, fix it when you build auth-gated features or before shipping to real users.

---

## Task-by-task: premature optimization or not?

### Task 01: Project Page Redesign — NOT premature. Do now.

This is not optimization at all. It's finishing incomplete work. The pages dump raw JSON and have no navigation links to the story editor. You literally cannot use the app through the UI without this. Every subsequent phase you build will need the project page to link into it. This is prerequisite infrastructure.

The mutation response typing fix (`Record<string, unknown>` -> `StoryResponseSchema`) and the navigate-after-create are both needed to make the "create story then edit it" flow work. Without this, you'll keep using the URL bar manually to test new phases.

Verdict: **Do this first. It unblocks everything.**

### Task 02: Route Path Standardization — Borderline. Lean toward doing it now, but keep it minimal.

The core argument is sound: `/story/:projectId` and `/story/:storyId/create` having different entities at the same URL depth is confusing and will get worse as you add more phases. When you add `/story/:storyId/characters` or `/story/:storyId/panels`, the ambiguity compounds.

However, the full proposal (path helpers, `ROOT_PATH` constant, Option A vs B debate) is more ceremony than you need right now. Here's what actually matters:

- Pick a nesting scheme that won't need to change when you add phases. Option A (`/story/:projectId/s/:storyId`) works fine.
- Update the 3 route definitions and the handful of `<Link>` / `useNavigate` calls.
- Don't build a path helper factory yet. You have ~5 path references total. A `ROOT_PATH` constant is fine. `storyPaths.project(id)` is overkill for 5 usages.

Verdict: **Do the route restructuring now (it gets harder with more code), skip the helper factory until you have 10+ path references.**

### Task 03: Query Key Cleanup — Partially premature.

Two parts to this:

**Do now:** Replace `["batman"]` with something that includes `storyId`. This is not about cleanliness — it's a correctness bug. Right now if a user has two stories and switches between them, the cache key is the same and they'll see stale stream data from the other story. When you add a second phase that also streams, this breaks further. The fix is 5 lines: change the key to include `storyId` in `useStoryPhase.ts` and `eventRouter.ts`.

**Hold off:** The unified key factory (`storyKeys.all`, `storyKeys.projects()`, `storyKeys.project(id)`, `storyKeys.stream(id)`) is nice-to-have. You have 3 disconnected query key objects across 3 files. That's fine for now. When you add phase 2 and suddenly have 6-8 query key groups, consolidating them will be obvious and easy. Doing it now means you're guessing at the key structure for phases you haven't built yet.

**Hold off:** Deleting the dead code in `story-phase.queries.ts` — sure, delete it, takes 30 seconds, but don't make it a tracked task. Just do it in passing when you're in those files for task 01 or 02.

Verdict: **Fix the `["batman"]` -> `storyKeys.stream(storyId)` now (it's a bug). Skip the full factory consolidation until phase 2 is in progress.**

### Task 04: Folder Reorganization — Premature. Hold off.

This is the most classically premature task of the four. The proposed structure is well-thought-out but speculative. It's designed around 6 phases that don't exist yet. Right now you have:

- `Projects/` (flat) — 5 files
- `StoryPhase/` (layered) — 7 files
- `events/` — 2 files
- 3 root files

That's 17 files. The proposed structure adds `phases/`, `api/` at root, renames and moves everything, and sets up slots for `character-extraction/`, `character-generator/`, etc. You'd touch every import in every file for a structure that serves future phases that don't exist.

The practical problems the reorg solves:
1. "Projects/ lacks api/ui separation" — Projects/ has 5 files. The split adds folders with 1-2 files each. Not worth it yet.
2. "Duplicate type definitions" — Real issue. Fix it by deleting the duplicates in `story-phase.types.ts` and importing from `Projects/types.ts`. That's a 2-line fix, not a reorg.
3. "Dead code" — Delete it. Not a reorg task.
4. "events/ is StoryPhase-specific" — True, but you don't know what the generic version looks like until you have a second phase's events to generalize from. Premature abstraction.
5. "No shared types location" — Create `api/story.types.ts` at the feature root when the second consumer appears. Don't preemptively build the folder.

The risk: you reorganize now, then when building phase 2 you discover the structure doesn't quite fit (maybe phases share more than expected, or less), and you reorganize again.

Verdict: **Hold off until you're actively building phase 2. At that point the right structure will be obvious from real needs, not guesses. For now, just fix the duplicate types and delete dead code as drive-by cleanup.**

---

## Summary: what to do now vs. later

### Do now (before building next phases)
1. **Task 01: Project page redesign** — Full execution. This is blocking basic usability.
2. **Task 02: Route restructuring** — Pick a nesting scheme and update the 3 routes + links. Skip the helper factory.
3. **Task 03 (partial): Fix `["batman"]`** — Replace with a key that includes `storyId`. Fix the bug.

### Do when building phase 2
4. **Task 03 (rest): Unified key factory** — Consolidate when you see the real shape of phase 2's cache needs.
5. **Task 04: Folder reorganization** — Restructure when you have two phases to inform the layout. Move `StoryPhase/` into `phases/story-phase/` as part of adding `phases/character-extraction/`.

### Drive-by (do whenever you're editing nearby files)
- Delete dead code in `story-phase.queries.ts`
- Delete duplicate types in `story-phase.types.ts` (import from `Projects/types.ts`)
- Delete `utils.tsx` after task 01 removes `recursivePrinter` usage
- Delete `projectHomeQueryKeys.story()` (defined, never used)

---

## Backend note for future reference

When you build v2 endpoints for the remaining phases (character extraction, character rendering, panel generation, panel rendering), the v1 `phases.py` has all the logic — it uses `generation/` classes (`CharacterExtractor`, `CharacterRenderer`, `PanelGenerator`, `PanelRenderer`, `BulkPanelGenerator`). The v2 equivalents will need to:

1. Use the `Repository` + `Service` pattern (like `v2/story.py` does) instead of `ProjectStateManager`
2. Use `EventEnvelope` streaming instead of `SimpleEnvelope`
3. Work with the relational models (Story, Character, ComicPanel) instead of the JSONB `ConsolidatedComicState`

The `generation/` classes themselves may need refactoring since they currently read/write to `ConsolidatedComicState`. That's a backend task, but it's for when you build those phases — not now.
