# Where the Current UX Doesn't Work (And Why)

**Date**: 2026-02-23  
**Context**: Honest assessment of the comic-builder stepper and story feature two-panel split

---

## The Comic-Builder Stepper: Death by Linearity

### What it does
Six phases in a horizontal pill bar: write-story -> extract-characters -> generate-characters -> generate-panels -> render-panels -> export-panels. User clicks through sequentially.

### Why it fails

**1. It treats creative work as a manufacturing pipeline.**
Assembly lines are sequential: part A must be complete before part B begins. Creative work is iterative: you write a story, extract characters, realize a character doesn't work, go back to the story, adjust, re-extract. The stepper allows free navigation (you can click any phase) but the mental model says "step 1, step 2, step 3." The affordance lies about the nature of the work.

**2. Context is destroyed at every phase transition.**
When you move from "Extract Characters" to "Generate Characters," the story text disappears. You're looking at character cards in isolation. When you move to "Generate Panels," the characters disappear. Each phase is a full-screen takeover. You can never see the story and the characters at the same time. This forces the user to hold context in their head instead of on the screen.

**3. Variations don't exist.**
Each character has one render. Each panel has one render. Re-rendering overwrites. There is no history, no comparison, no "try another." The user's creative options are: accept or redo. There is no "explore."

**4. The phases are the wrong abstraction.**
"Extract Characters" and "Generate Characters" are two separate phases in the stepper, but from the user's perspective, they're one action: "show me my characters." The technical distinction (extraction = text analysis, generation = image rendering) is an implementation detail leaking into the UX.

**5. No dependency awareness.**
If you go back to phase 1 and change the story, phases 2-6 still show the old data. Nothing indicates staleness. The user must manually remember "I changed the story, so I need to re-extract characters, re-generate them, re-generate panels, re-render panels." The system provides no help.

**6. The empty state for each phase is confusing.**
Jump to "Render Panels" before generating panels, and you see... nothing. No guidance, no explanation, no redirect. Just an empty screen with a button that does nothing useful.

---

## The Story Feature Two-Panel Split: Death by Narrowness

### What it does
Left panel (35%): chat-like prompt history. Right panel (65%): story text artifact. Mobile: toggle between the two views.

### Why it fails

**1. It solves only one phase.**
The two-panel split works for story generation. But it has no answer for "what happens next?" Where do characters go? Where do scenes go? The layout is designed for a single input-output pair (prompt -> story). The engine produces a graph of artifacts, not a single output.

**2. The split is backwards for mobile.**
On mobile, 90% of users, you can only see one panel at a time. So you're either looking at your prompts (useless without the story) or looking at the story (useless without the ability to refine it). The toggle adds friction to every interaction: read story, switch to prompt panel, type refinement, switch to story panel, read result. Four taps for one refinement.

**3. Chat is the wrong metaphor.**
The left panel shows prompts as chat messages. But this isn't a conversation. The user isn't having a dialogue with the AI. They're sculpting an artifact. Chat implies back-and-forth; the reality is prompt-and-refine. Chat messages accumulate linearly; creative refinements branch. The metaphor misleads.

**4. It doesn't scale to the XYZ model.**
The Y-axis (flow) has no representation -- there's only one artifact type (story). The X-axis (variation) has no representation -- there's only one story text that gets replaced. The Z-axis (projection) has no representation. The layout is 2D at best and doesn't have a conceptual extension point for the third dimension.

---

## What Both Approaches Share (The Common Failure)

**They both separate "seeing" from "doing."**

In the stepper: you see the result in one phase, but you act on it (refine it) in a different phase or by navigating back.

In the two-panel: you see the result on the right, but you act on it on the left.

The Timeline River approach corrects this: **seeing and acting happen in the same place.** You see the character card, you tap it, you refine it, you see the new version -- all in one spatial context. The artifact and its refinement controls are co-located.

This is Norman's "gulf of execution" principle: minimize the distance between the user's intention and the action that fulfills it. In the current UX, the gulf is spatial (navigate to the right panel/phase to act) and temporal (wait for context switch). In the proposed UX, the gulf is one tap.

---

## What's Worth Keeping

Not everything is wrong. Some patterns from the current implementations are strong:

1. **Streaming text display** (story feature): Watching text appear character-by-character is satisfying and communicates "the AI is working." Keep this.

2. **The shadcn/ui component system**: Clean, consistent, accessible. The visual language is right -- minimalist, no clutter. Keep all of it.

3. **React Query for server state** (story feature): The EventRouter pattern of writing SSE chunks directly into the query cache is architecturally sound. Keep this for all streaming artifacts.

4. **Mobile view toggle as a concept** (story feature): The idea of adapting to mobile with a toggle is right. The execution (toggling between two halves of a split view) is wrong. But the bottom sheet pattern proposed in the Timeline River is the same principle done better.

5. **Project/Story entity hierarchy** (story feature): Projects contain stories. Stories are URL-addressable. This clean entity model survives intact into the new architecture.

6. **The v2 API and EventEnvelope protocol** (story feature): The structured, versioned, typed event system is ready for multi-phase streaming. No changes needed on the protocol layer.
