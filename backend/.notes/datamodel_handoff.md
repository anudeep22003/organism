# Data Model Restructure — Handoff Document

## Context

The existing data model stored the entire comic builder state as a single JSONB column. This restructure normalizes it into proper relational tables while keeping pragmatic denormalization where it makes sense (JSONB for flexible attribute bags, arrays for simple lists).

---

## Iteration 1: Decoupling Characters from Stories

### What was
Character had a `story_id FK` — each character belonged to exactly one story.

### The analogy
A story is like a movie. Characters are like actors. An actor doesn't belong to a single movie — they exist independently and get **cast** into movies.

### What changed
- Removed `story_id` from Character
- Added `StoryCharacter` junction table with composite PK `(story_id, character_id)`
- Added `PanelCharacter` junction table with composite PK `(panel_id, character_id)`
- Removed `string[] characters` from ComicPanel (replaced by PanelCharacter)

### Why
- A character can be cast in multiple stories (reusable across projects)
- A story has multiple characters (cast list)
- A panel features multiple characters (call sheet for a scene)
- Each pairing is unique — an actor can't appear twice in the same cast/scene
- This is a standard many-to-many relationship enforced by composite primary keys

### Design decision: Character ownership
Characters are decoupled from both Project and Story. They live at the user level (`user_id FK` on Character). A user has a "roster" of characters they can cast into any story.

---

## Iteration 2: Artifact → RenderJob

### What was
`Artifact` was a static output record — just a URL and a status. It had no memory of how it was produced.

### The reframe
Instead of thinking of it as a static artifact, think of it as a **render job**. A render job has:
- **Initiator** — the entity that triggered the render (character or panel, via polymorphic `renderable_id` + `renderable_type`)
- **Inputs** — reference images, prompts, style cues (what went into the generation)
- **Output** — the generated image URL

This matches how image generation models actually work: you gather inputs, submit a job, get an output.

### What changed
- Renamed `Artifact` → `RenderJob`
- Renamed `url` → `output_url` (explicit: this is the generated output)
- Added `jsonb inputs` — a snapshot of what was used for this render (reference URLs, prompts, etc.)

### Why
- Captures lineage: you know what produced each render
- Supports reproducibility: re-run with the same inputs
- Natural place to hang job lifecycle state (status tracking)
- The "inputs" field is JSONB for now — avoids committing to a junction table structure until the query patterns are clear

---

## Iteration 3: Reference Images on Character

### What we considered
A dedicated `CharacterReference` table (`id`, `character_id`, `url`) for reference images. Fully normalized, one row per image.

### What we chose instead
`jsonb reference_image_urls` directly on Character — a simple JSON array of URL strings.

### Why
- Reference images are just a list of URLs with no per-image metadata needed right now
- A junction table adds query and migration complexity for no current benefit
- Easy to promote to its own table later if per-reference metadata (labels, ordering, source) becomes necessary
- Follows the principle: don't add structural complexity until you have a reason

### How it connects to RenderJob
Reference images **belong** to the character (ownership), but are **consumed** by render jobs (usage). The character's `reference_image_urls` is the source of truth for "what does this character look like." The render job's `jsonb inputs` captures a snapshot of which references were actually used for a specific generation — because references may change over time, and you want to know what produced a given output.

---

## Iteration 4: Removing streaming_status from Data Entities

### What was
`streaming_status` existed on Story, Character, ComicPanel, and Artifact. It tracked states like idle/streaming/completed/error.

### The insight
- The backend only signals the **end** of a stream
- Intermediary states (loading, streaming) are maintained by the **frontend**
- This makes it UI state, not server state
- For data entities: if extraction fails, the row simply doesn't exist — absence is the signal
- For cancelled requests: the backend aborts the stream and doesn't persist — no orphaned status to clean up

### What changed
- Removed `streaming_status` from Story, Character, and ComicPanel
- Kept `status` on RenderJob (renamed to `render_job_status`)

### Why keep it on RenderJob?
RenderJob is the one entity where status is genuinely **server-side state**. It represents async work submitted to an external image generation API. The backend manages the lifecycle: queued → processing → completed/failed. A missing `output_url` alone is ambiguous (still processing? or failed?) — you need explicit status.

### Why remove it from everything else?
For Story/Character/ComicPanel, the data itself is the status:
- Row doesn't exist → not generated yet
- Row exists with data → generation completed
- Row exists with partial data → shouldn't happen (backend only persists on completion)

---

## Final Model Summary

| Entity | Purpose | Key Design Choice |
|---|---|---|
| **Project** | Top-level container | Owned by user, 1:1 with Story |
| **Story** | The narrative | Belongs to a project |
| **Character** | Reusable actor | Owned by user (not story/project), cast into stories via junction |
| **StoryCharacter** | Cast list | Composite PK, many-to-many |
| **ComicPanel** | A scene in the story | Ordered within a story |
| **PanelCharacter** | Scene call sheet | Composite PK, many-to-many |
| **RenderJob** | Image generation job | Polymorphic initiator, captures inputs + output, has lifecycle status |

### Patterns used
- **Junction tables with composite PKs** for many-to-many (StoryCharacter, PanelCharacter)
- **Polymorphic association** for RenderJob → Character/Panel (`renderable_id` + `renderable_type`)
- **JSONB for flexible bags** — character attributes, project metadata, render inputs, reference image URLs
- **Status only where it's server state** — RenderJob only

### Guiding principles applied
- Simplicity: least changes, no premature structure
- Flexibility: JSONB where schema is uncertain, junction tables where relationships are certain
- Explicitness: `output_url` not `url`, `render_job_status` not `status`
- No premature optimization: `reference_image_urls` as JSONB instead of a table, `inputs` as JSONB instead of a junction
