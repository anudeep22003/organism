# XYZ Narrative Engine UI Options (Agency Brief)

Date: 2026-02-23
Audience: Product + Design + Frontend
Tone target: Simplicity first, power through structure

## 1. What We Are Solving

You are not building a chat app and not building a stepper wizard.
You are building a spatial creative instrument with three axes:

- `Y` axis: Flow (story -> characters -> scenes -> projections), infinitely scrollable
- `X` axis: Variation (alternatives for the same node)
- `Z` axis: Layers/Projection (comic/audio/video/other views over the same narrative state)

The UI must feel simple at first touch, but should grow without redesign.

## 2. Audit Reality (From Current Frontend)

### Old model (`frontend/src/pages/comic-builder`)

- Stepper hard-codes phases and encourages linear manufacturing behavior.
- State shape has one canonical story, one character object per id, one panel object per id (`consolidatedState.ts`), not explicit variation sets.
- Phase transitions remove context (story disappears while editing characters, etc.).
- No explicit stale/dependency signaling in the interface.

### New partial model (`frontend/src/features/story`)

- Split prompt/artifact works for one artifact type only.
- Mobile forces toggle between prompt and artifact, creating frequent context switches.
- Stream architecture is solid (event router + cache updates), but interaction model is still prompt-thread oriented, not node-graph oriented.

## 3. First Principles (Norman + Ive + Jobs Synthesis)

- One primary spatial metaphor: a single vertical workspace.
- One clear meaning per axis:
  - Vertical = structure
  - Horizontal = alternatives
  - Depth = medium/layer
- Keep signifiers visible on touch devices (no hover-only behavior).
- Co-locate seeing and doing: refinement controls live on/near the artifact they modify.
- Preserve reversibility: creating variation never destroys parent.
- Reveal complexity progressively, never upfront.

## 4. Axis Decision: Variation Must Stay on X (Not Z)

Use `X` for variation. Keep `Z` for projection/layers.

Why:

- Users already interpret left/right as "other options of same thing".
- `Z` is harder to visualize on mobile and better reserved for "same scene, different medium".
- If variation moves to Z, you lose an intuitive gesture vocabulary.

Rule:

- `X` = "another attempt of this node"
- `Z` = "another representation of this node"

Example:

- Character Kael v1/v2/v3 = X-axis
- Character Kael shown as text profile vs rendered portrait vs animation reference = Z-axis

## 5. Interaction Contract (How Variation Is Created)

For every modifiable node:

1. User taps `Refine` (always visible).
2. Bottom sheet opens with:
   - current version context
   - short prompt history
   - pinned prompt input
3. User submits natural-language ask.
4. System creates `new variation` to the right (`v+1`), keeps old version.
5. Dependent descendants are marked `stale`, never auto-regenerated.

This is the essential loop. Keep it identical across Story, Character, Scene, Panel prompt metadata.

---

## 6. Four UI Pattern Options

## Option A: Vertical Spine + Inline Node Tracks (Recommended Baseline)

Single long document. Each node in the vertical spine owns a local horizontal variation track.

### Mobile sketch

```text
+----------------------------------+
| Project                          |
+----------------------------------+
| STORY                            |
| [ story text preview ]   [Refine]|
| v2 of 3   <  >                   |
|----------------------------------|
| CHARACTER: Kael                  |
| [portrait]                       |
| [brief description]      [Refine]|
| v1 of 2   <  >                   |
|----------------------------------|
| SCENE 1                          |
| [scene text + panel thumb]       |
| v1 of 1                  [Refine]|
|----------------------------------|
| SCENE 2   [STALE]                |
| ...                              |
+----------------------------------+
```

### Desktop sketch

```text
+--------------------------------------------------------------+
| STORY card (active variation)                                |
| [<] v2 of 3 [>]                              [Refine]        |
+--------------------------------------------------------------+
| CHARACTER Kael                                                    |
| [<] v1 of 2 [>]   [portrait + text]               [Refine]       |
+--------------------------------------------------------------+
```

### Strengths

- Very clear Y/X mapping.
- Fastest to implement from current code direction.
- No mode switch required to refine.
- Easy stale marking by vertical descendants.

### Scaling risks

- Long projects become very tall.
- Many siblings (e.g., 20 characters) inflate vertical noise.

### Mitigation

- Add collapsible section wrappers above repeated node types.
- Add "jump to section" floating index on mobile.

---

## Option B: Layer Bands (Timeline River)

Vertical bands are layers (`Story`, `Characters`, `Scenes`, `Output`). Inside each band, items scroll horizontally. Variation exists in item detail.

### Mobile sketch

```text
+----------------------------------+
| STORY                            |
| [single story card]    [Refine]  |
+----------------------------------+
| CHARACTERS                 [+]   |
| [Kael] [Lyra] [Maren] [..] ->    |
+----------------------------------+
| SCENES                     [+]   |
| [Sc1] [Sc2] [Sc3] [..] ->        |
+----------------------------------+
| OUTPUT                           |
| [Panel1] [Panel2] [Panel3] ->    |
+----------------------------------+
```

Tap an item -> bottom sheet for versions + prompt.

### Strengths

- Best overview density for mobile.
- Feels familiar (rail browsing patterns).
- Scales better than pure node stack for large collections.

### Scaling risks

- Dependency direction can feel implicit, not explicit.
- Horizontal rails hide off-screen items.

### Mitigation

- Add per-band stale counters (`Scenes: 3 stale`).
- Add quick filters and search inside each rail.

---

## Option C: Focus Canvas + Minimap Flow

One active node fills most of screen; flow shown as compressed minimap/timeline. Best for deep editing sessions.

### Mobile sketch

```text
+----------------------------------+
| Flow map: Story > Char > Scn...  |
+----------------------------------+
| ACTIVE NODE: Character Kael      |
| [large artifact view]            |
| [variation scrubber: v1 v2 v3]   |
| [Refine prompt pinned bottom]    |
+----------------------------------+
```

### Strengths

- Highest focus, low clutter.
- Good for power users doing iterative refinement loops.

### Scaling risks

- Weak at-a-glance sense of whole project.
- More navigation overhead for casual users.

### Mitigation

- One-tap jump back to full flow view.
- Keep minimap always visible.

---

## Option D: Dual Mode (Compose vs Explore)

`Compose` = clean vertical flow for creation.
`Explore` = graph view with dependency edges for advanced stale impact reasoning.

### Explore sketch

```text
Story v2
  |
  +--> Character Kael v3 ----> Scene 2 v1 ----> Panel 4 v1
  |            \                   |
  |             +--> Scene 5 v2 ---+
  +--> Character Lyra v1
```

### Strengths

- Best for future platform-grade dependency visibility.
- Makes stale propagation and rerender targets explicit.

### Scaling risks

- Too complex as primary mode for consumer mobile.
- Graph interaction on phone is difficult.

### Mitigation

- Keep graph mode secondary and optional.
- Default everyone to Compose mode.

---

## 7. Mobile-First Rules (Non-Negotiable)

- No hover-required control.
- Every modifiable artifact has visible `Refine` affordance.
- Prompt input must be pinned in thumb reach (bottom sheet/footer).
- Never force prompt/artifact split toggle for core loop.
- Keep to one major scroll direction per context:
  - flow view: mostly vertical
  - variation view: mostly horizontal within one artifact

## 8. Dependency UX (How to Show Stale Without Panic)

Use three states only:

- `Fresh`
- `Stale` (amber indicator + reason)
- `Regenerating`

Display pattern:

```text
Scene 2  [STALE]
Reason: Character Kael changed in v3
Actions: [Regenerate] [Keep Current]
```

Global convenience:

- Per-section `Regenerate stale` action.
- Optional `Regenerate all downstream` from a changed node.

No auto-cascade rerender by default.

## 9. Recommended Path

### Product recommendation

Start with **Option A** for fastest conceptual clarity and implementation momentum.
Then evolve into **Option B hybrid** as collection sizes grow.
Reserve **Option D Explore mode** for advanced users/platform phase.

### Why this path

- Preserves your physics-grounded mental model immediately.
- Keeps mobile interactions intuitive and low-friction.
- Avoids early over-investment in graph UI while keeping architecture compatible.

## 10. What Will Break If We Get It Wrong

- If variation is hidden behind deep menus: users stop exploring alternatives.
- If prompt and artifact are spatially separated: refinement becomes slow and annoying.
- If stale is invisible: trust collapses (users export inconsistent outputs).
- If Z-axis is overloaded early: conceptual model becomes muddled.

## 11. Practical Next Design Deliverables

1. One-page interaction spec for the `Refine -> New variation -> Stale marking` loop.
2. Wireframes for Option A mobile + desktop (happy path + stale path).
3. Decision checkpoint after usability pass:
   - If users struggle with long scroll -> introduce Option B bands.
4. Keep a dormant Explore graph concept doc for platform stage.

