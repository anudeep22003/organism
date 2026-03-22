# ArtifactCard — Handoff Document

## What We Built

A generic, reusable `ArtifactCard` component that serves as the foundational UI primitive for the story workspace. It replaces the previous two-panel `StoryPhasePage` (prompt left, artifact right) with a vertical layout where each artifact — story, characters, scenes — gets its own card stacked in a single column.

### Files Created

| File | Role |
|---|---|
| `components/ArtifactCard/types.ts` | `ArtifactCardProps`, `RefinePayload` |
| `components/ArtifactCard/ArtifactCard.tsx` | The card shell — header, content, collapse, footer |
| `components/ArtifactCard/RefineInput.tsx` | Inline input with text, voice, and image attachment |
| `components/ArtifactCard/AttachmentPreview.tsx` | Thumbnail grid for staged files before submit |
| `components/ArtifactCard/index.ts` | Barrel export |
| `components/StoryContent.tsx` | Story-specific renderer (serif prose + streaming cursor) |
| `StoryPhase/StoryWorkspace.tsx` | Vertical layout page replacing StoryPhasePage |

### Files Removed

The old two-panel layout and all its components: `StoryPhasePage`, `ArtifactPanel`, `PromptPanel`, `PromptMessage`, `MobileViewToggle`.

---

## UX Decisions (Don Norman Lens)

### Expand/Collapse as Content Navigation, Not Action

We deliberately separated *navigation* (expand/collapse — changes your view) from *actions* (refine — changes the artifact). They look different because they are different.

- **Collapsed state**: The text fades out over ~3 lines with a gradient. The entire fade zone is the click target. A subtle centered chevron hints at "more" but doesn't demand attention. The gradient itself is the affordance — it communicates incompleteness without a label.
- **Expanded state**: A small floating button appears fixed in the bottom-right corner of the viewport. It follows you as you scroll through long content, always reachable. Uses an `IntersectionObserver` so it only appears when the card is in view. Nearly invisible at rest, reveals on hover.
- **Footer**: Reserved exclusively for actions (Refine). No view controls clutter it.

We tried consolidating expand/collapse and refine into a single footer row. It looked cleaner in code but violated the principle of natural mapping — putting navigation and mutation controls side by side suggested they were peers. They aren't. We reverted.

### RefineInput as the Central Input Surface

The refine input is the single point where users express intent about an artifact. It accepts three modalities:

1. **Text** — typed directly
2. **Voice** — recorded and transcribed via Whisper
3. **Images** — uploaded as reference attachments (when parent opts in)

This follows Norman's principle of consistency: same interaction zone, same submission flow, multiple input types. Users don't need to learn separate interfaces for "text refinement" vs "adding a reference image." It's all one gesture: open refine, provide input, submit.

The input opens inline at the bottom of the card (not a modal, not a separate panel). It's visually part of the card — separated by a subtle border-t. Escape dismisses it. This keeps the user in context with the artifact they're refining.

---

## State Architecture

### ArtifactCard State

```
ArtifactCard (local UI state only)
  ├── isRefineOpen: boolean      — is the input expanded
  ├── isExpanded: boolean        — is content fully visible
  ├── hasOverflow: boolean       — does content exceed 33vh
  └── isCardVisible: boolean     — IntersectionObserver for floating collapse
```

All view state. No data state. The card doesn't know what it's rendering.

### RefineInput State

```
RefineInput (transient input state)
  ├── text: string               — cleared on submit
  ├── stagedFiles: File[]        — cleared on submit
  └── useVoiceRecorder           — recording/transcribing/idle
```

All transient. Nothing persists after submit. The parent never sees files or text until the user explicitly sends them.

### Payload Contract

```ts
type RefinePayload = {
  text: string;
  attachments: File[];
};
```

Always the same shape. `attachments` is `[]` when not used. The parent decides what to do with the payload:

- **StoryWorkspace**: extracts `payload.text`, ignores attachments
- **Future CharacterCard**: would use both text and attachments

### Flexibility Model

The card uses **parent opt-in** for capabilities:

| Prop | Default | What it enables |
|---|---|---|
| `collapsible` | `false` | Fade gradient + expand/collapse |
| `enableAttachments` | `false` | Image picker in refine input |
| `onRefine` | `undefined` | Entire refine footer (no callback = no footer) |
| `isStale` | `false` | Amber "Needs update" badge |

Each prop is independently toggleable. A card can be collapsible without refine, or refineable without attachments. No capability implies another.

### What the Card Doesn't Own

- What content looks like (passed as `ReactNode`)
- What happens on refine (callback to parent)
- What to do with attachments (parent's responsibility)
- Upload logic, API calls, persistence (none of this is in the card)

The card is a shell. It provides structure (header, content, footer), interaction patterns (collapse, refine), and input collection (text, voice, files). Everything else belongs to the parent.

---

## Commits

1. `470d88b` — ArtifactCard component + vertical workspace layout
2. `ad41da3` — Collapsible content with fade gradient
3. `530ecb5` — Expand/collapse as content navigation (fade target + floating collapse)
4. `e1a680d` — Image attachment support in RefineInput
