# Character Extraction UX: Representation Options and Recommendation

Date: 2026-03-04  
Scope: `frontend/src/features/story` (new iteration only)  
Reference inputs: `ArtifactCard` handoff, `ux-*` explorations, old `CharacterCard` and phase flows

## 1. The Design Problem

You now have a strong primitive (`ArtifactCard`) and a working Story section.  
The next challenge is characters, where each character has at least two surfaces:

1. A structured object (extracted attributes, schema can evolve)
2. A projection (today image, later video/audio/etc.)

The core tension is this:
- Users need to inspect/refine the object.
- Users need to inspect/refine the render.
- Users should understand these are the same character, not separate entities.

## 2. North Star (Norman + Ive + Jobs Lens)

1. Keep one stable spatial model.
2. Keep cause and effect visible.
3. Keep the beginner path obvious.
4. Keep expert control available but quiet until needed.
5. Never force users to remember hidden state.

Translated into product behavior:
- The character object is the source of truth.
- The render is a projection of that source.
- Refinement is always close to what it changes.
- Users can see object + projection together when needed.

## 3. Recommended Conceptual Model

Treat each character as a **paired artifact**:

```text
Character (canonical)
  id
  attributes: Record<string, unknown>      <-- evolving schema
  references: upload/image links (optional)
  versions: attribute lineage
  projections:
    portraitImage[]                        <-- now
    motionClip[]                           <-- later
```

Important distinction:
- `X` axis: versions/alternatives (v1, v2, v3)
- `Y` axis: flow (story -> characters -> scenes)
- `Z` axis: projection type (attributes/text, image, video, etc.)

Key decision: `Z` is a semantic depth model, not always a visual stack.  
You can render `Z` side-by-side for clarity while still preserving depth conceptually.

## 4. Representation Options

## Option A: Surface Tabs Inside One Card

Single character card with tabs:
`[Attributes] [Render] [History]`

```text
+--------------------------------------+
| Kael                      v2   [..]  |
| [Attributes] [Render] [History]      |
|                                      |
| (active tab content)                 |
|                                      |
|                           [Refine]   |
+--------------------------------------+
```

Pros:
- Very compact.
- Easy to implement on top of existing `ArtifactCard`.
- Works well when space is constrained.

Cons:
- Hides object/render relationship unless user switches tabs.
- Comparison is sequential, not simultaneous.

Best for:
- Early MVP speed.

---

## Option B: Split Pair (Attributes + Render Together)

Two synchronized surfaces shown together by default.

Desktop:
```text
+-----------------------------------------------------------+
| Kael                                           v2   [..]  |
| +----------------------+ +------------------------------+ |
| | Attributes           | | Render                       | |
| | name: Kael           | | [ portrait image ]           | |
| | demeanor: stoic      | | prompt: "older, weathered"   | |
| | markers: cheek scar  | | status: generated            | |
| +----------------------+ +------------------------------+ |
|             [Refine Attributes] [Refine Render]          |
+-----------------------------------------------------------+
```

Mobile:
```text
+---------------------------+
| Kael               v2     |
| [Render Preview]          |
| [Key Traits Summary]      |
| [View Pair ->]            |
+---------------------------+
```

Tap opens bottom sheet with stacked pair:
```text
[Render]
[Attributes]
[Refine Attributes] [Refine Render]
```

Pros:
- Highest clarity: cause/effect is visible.
- Great for personal story workflow (does this look like me/friend?).
- Makes schema edits feel meaningful immediately.

Cons:
- Heavier layout.
- Needs careful responsive behavior.

Best for:
- Your stated beginner flow and trust-building.

---

## Option C: Flip Card (Literal Z-Layer)

Card flips between front (render) and back (attributes).

Pros:
- Strong metaphor for layers/depth.
- Visually memorable.

Cons:
- Poor side-by-side comparison.
- Feels ornamental if used for every edit.
- Can increase cognitive load and motion fatigue.

Best for:
- Occasional flourish, not primary control surface.

---

## Option D: Rail + Inspector (Overview + Focus)

In Characters rail, cards stay compact.  
Selecting a card opens detail inspector (sheet/panel) showing full pair and controls.

```text
CHARACTERS RAIL: [Kael] [Lyra] [Maren] [+]

Inspector:
[Render large]
[Attributes editor]
[Reference images]
[Refine input + uploads]
[Version controls]
```

Pros:
- Scales well for many characters.
- Keeps overview clean.
- Aligns with your existing Timeline River explorations.

Cons:
- Needs one more interaction step (tap card -> inspect).

Best for:
- Medium/large projects and power-user depth.

---

## Option E: Adaptive Pair (Beginner -> Pro Progression)

Stage-aware UI behavior:
1. Pre-render: attributes-first
2. First render exists: paired view
3. Multiple versions: add version rail + history

Pros:
- Excellent progressive disclosure.
- Avoids overwhelming first-time users.

Cons:
- More state-dependent UI rules.

Best for:
- Your desired "simple first, deep later" product strategy.

## 5. Recommendation: Hybrid of B + D + E

Recommended baseline:
1. Use **rail overview** for character collection (`Option D`).
2. Use **paired detail surface** in sheet/panel (`Option B`).
3. Use **adaptive disclosure** by maturity of each character (`Option E`).

Why this is the best fit:
- Reuses your existing spine/river direction.
- Preserves "object is source, render is projection."
- Keeps beginner flow obvious while still serving pro controls.

## 6. How to Resolve the Z-Axis Question

Your concern is valid: if text/render are in depth, how can they be side-by-side?

Resolution:
- Keep depth in the **data model** (projection layers).
- Use side-by-side in the **presentation model** when clarity is needed.
- Let users switch projection focus without losing paired context.

Practical rule:
- Default: show both (paired).
- Focus mode: user can maximize one surface.
- Never force a hard either/or toggle for core editing.

## 7. Character Refinement Flow (Beginner Path)

1. User taps `Extract Characters`.
2. Characters appear with structured summaries only.
3. User taps a character -> inspector opens.
4. User edits/refines attributes and optionally uploads references.
5. User taps `Render`.
6. Image appears beside attributes.
7. User refines image (prompt + uploads) until satisfied.
8. User confirms character as "ready."

Beginner guardrails:
- One clear CTA at a time (`Render Character`, then `Continue to Scenes`).
- Keep advanced controls collapsed.

## 8. Pro Controls (Progressive Disclosure)

Collapsed by default under `Advanced`:
- Raw attribute object editor (key/value or JSON mode).
- Field-level lock controls (lock face, keep palette, etc.).
- Prompt lineage and version compare.
- Multi-reference management (primary vs secondary reference).
- Render settings (style strength, seed, aspect, model).

## 9. ArtifactCard Reuse Strategy

Keep `ArtifactCard` as shell; extend content composition.

Current strengths to retain:
- Header/status/needs-update semantics
- Collapsible behavior
- Inline `RefineInput` with text + voice + uploads

Needed extension points:
1. Multiple refine intents:
   - `attributes`
   - `projection` (image today, video later)
2. Surface switch/focus controls in card header
3. Optional paired layout renderer in content area

Proposed payload extension:

```ts
type RefineTarget = "attributes" | "projection";

type CharacterRefinePayload = {
  target: RefineTarget;
  text: string;
  attachments: File[];
};
```

This keeps the existing contract shape but adds intent routing.

## 10. Suggested UI Structure in `features/story` (No Legacy Changes)

Potential components:

```text
components/
  CharacterRailSection.tsx
  CharacterCardPreview.tsx
  CharacterInspector/
    CharacterInspector.tsx
    CharacterPairView.tsx
    CharacterAttributesView.tsx
    CharacterProjectionView.tsx
    CharacterVersionRail.tsx
```

How it fits:
- Story remains top artifact.
- Characters becomes a rail section.
- Tap item opens inspector (mobile sheet / desktop side panel).
- Inspector uses paired view and reuse of `RefineInput`.

## 11. Visual Behavior Rules (Keep Experience Calm)

1. If no render exists, render panel shows a clear empty state with one CTA.
2. When render arrives, crossfade placeholder -> image (no jarring jumps).
3. When attributes change, show "projection may be stale" badge on image.
4. Keep stale indicators amber/informational, never blocking.
5. Keep refinement controls in thumb-reach (bottom area on mobile).

## 12. Decision Matrix

| Option | Beginner Clarity | Pro Depth | Scale (many chars) | Implementation Cost | Recommendation |
|---|---:|---:|---:|---:|---|
| A Tabs | Medium | Medium | Medium | Low | Good fallback |
| B Split Pair | High | High | Medium | Medium | Strong core |
| C Flip | Low | Low | Medium | Medium | Avoid as primary |
| D Rail + Inspector | High | High | High | Medium | Must-have structure |
| E Adaptive Pair | High | High | High | Medium-High | Add incrementally |

## 13. Phased Rollout

Phase 1 (fast, high impact):
1. Characters rail + inspector shell
2. Attributes view + refine with uploads
3. Render panel + generate action

Phase 2:
1. Paired view polish (sync highlights, stale badges)
2. Version rail and prompt lineage
3. Section-level stale/refresh actions

Phase 3:
1. Advanced controls drawer
2. Projection switcher foundation (`Image`, future `Video`)

## 14. Final Recommendation

Ship **Rail + Inspector with Paired Surfaces** as the baseline.

This gives you:
- Simple beginner experience
- Clear object/render pairing
- Strong future path for Z-axis projections
- Reuse of `ArtifactCard` and current refinement primitives

If you need one sentence product definition for this phase:

**"A character is one object with multiple projections; the UI always lets users shape the object and evaluate the projection in one place."**
