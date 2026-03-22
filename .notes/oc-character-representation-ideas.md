# Character Representation: The Dual-Nature Problem

**Date**: 2026-03-04  
**Presented by**: The studio of Norman, Ive & Jobs  
**Client brief**: How to represent characters that exist first as structured text (extracted attributes) and later as rendered images, with refinement at both levels, in a way that doesn't wall-of-text the user or create cognitive burden.

---

## The Problem, Precisely Stated

A character has a **dual nature**:

1. **The Description** — a structured object of attributes (name, role, era, visualForm, colorPalette, distinctiveMarkers, demeanor, brief). This is the soul. It's what the AI extracted. It's editable, refinable, and always present.

2. **The Render** — an image. A portrait. A face. This is the projection of the description into visual form. It arrives later. It may not arrive at all (the user might skip it). When it does arrive, it becomes the primary thing the user cares about.

The problem: **these two things are a pair, but they compete for the same space.** The description is text-heavy. The render is visual. Showing both at once risks clutter. Showing only one risks losing the other.

And there's a lifecycle dimension: characters start as text-only (extracted), become text+image (rendered), and the user may refine either layer independently — change the description (which stales the image) or regenerate the image (which doesn't change the description).

Your instinct about layers (text layer and render layer, Z-axis as projection) is correct in principle. The question is what this means in practice on a 375px screen.

---

## The Beginner Flow (The North Star)

Before exploring UI patterns, let's be clear about what the simple path must feel like:

1. User has a story
2. They tap "Extract Characters" (or the suggestion nudge does it)
3. Characters appear — they see names and key traits
4. They can optionally upload reference photos ("this is what Kael looks like — he's my friend")
5. They can optionally refine descriptions ("make her older, add a scar")
6. They tap "Render" (or system suggests it)
7. Portraits appear — the characters now have faces
8. They can refine the portraits ("more weathered", or upload a better reference)

**The beginner never thinks about "text layer" vs "image layer."** They think: "here's my character, here's what they look like." The dual nature must be invisible to beginners and discoverable by pros.

---

## Part 1: The Character Card — Five Approaches

These are approaches for how a single character appears in the Characters rail/section of the workspace. Each approach handles the text-to-image transition differently.

---

### Approach A: "The Flip Card" — Front and Back

**Metaphor**: A playing card. The front shows the render (image). The back shows the attributes (text). You flip between them.

```
TEXT SIDE (initial state, no render yet):

+------------------+
|                  |
|  Kael            |
|  ──────          |
|  Warrior-Poet    |
|  Era: Ancient    |
|  Demeanor: Stoic |
|                  |
|  [Render ->]     |
+------------------+

IMAGE SIDE (after render):

+------------------+
|  +-----------+   |
|  |           |   |
|  | [portrait]|   |
|  |           |   |
|  +-----------+   |
|  Kael            |
|  v1   [flip ->]  |
+------------------+

Flip gesture reveals the text side:

+------------------+
|                  |
|  Kael            |
|  ──────          |
|  Warrior-Poet    |
|  Era: Ancient    |
|  Demeanor: Stoic |
|                  |
|  v1  [<- flip]   |
+------------------+
```

**Lifecycle**:
- Pre-render: Card shows text side only. No flip affordance.
- Post-render: Card defaults to image side. Flip icon appears. Tap to see attributes.
- The card "upgrades" when the render arrives — it flips to show the new face.

**Norman**: "The flip is a natural mapping — physical cards have two sides. The transition from text-only to image-primary mirrors the creative progression. But: the flip hides one side completely. You can never see both."

**Ive**: "The animation of the flip is the moment of delight. The character gets a face. It's a reveal. But flipping back and forth to compare description to image is tedious."

**Jobs**: "People will flip once to see the face, then never flip back. The text side dies. That's a problem if the attributes matter."

**Verdict**: Elegant metaphor, wrong for a working tool. The text side becomes invisible.

---

### Approach B: "The Portrait with Caption" — Image Over Text

**Metaphor**: A portrait in a gallery. The image dominates. Below it, a name plate with key attributes.

```
PRE-RENDER (text only):

+------------------+
|  +------------+  |
|  |            |  |
|  |    [?]     |  |
|  |  no image  |  |
|  |            |  |
|  +------------+  |
|  Kael            |
|  Warrior-Poet    |
|  [Render]        |
+------------------+

POST-RENDER:

+------------------+
|  +------------+  |
|  |            |  |
|  | [portrait] |  |
|  |            |  |
|  +------------+  |
|  Kael            |
|  Warrior-Poet    |
|  v1              |
+------------------+
```

The card always has the same layout: image area on top, name + one-line summary below. Pre-render, the image area shows a placeholder (silhouette, initials, or a gentle "?" mark). Post-render, the portrait fills in.

**Full attributes are only in the detail view** (bottom sheet on mobile, side panel on desktop). The card in the rail is a summary — the poster, not the dossier.

```
DETAIL VIEW (bottom sheet):

+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                            |
|  Warrior-Poet of Vereth          |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |    [portrait image]        |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  [< prev]  o *o*  [next >]      |
|            v2 of 2               |
|                                  |
|  --- Attributes ---------        |
|  Role: Protagonist               |
|  Era: Ancient                    |
|  Visual Form: Tall, lean...      |
|  Color Palette: Storm grey...    |
|  Distinctive Markers: Scar...    |
|  Demeanor: Stoic, poetic         |
|                                  |
|  --- References ----------       |
|  [uploaded photo 1] [photo 2]    |
|                                  |
|  +----------------------------+  |
|  | How should Kael change?    |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
+----------------------------------+
```

**Norman**: "This is progressive disclosure done right. The card shows what you need to recognize the character (face + name). The detail view shows what you need to work with the character (attributes + history + refine). Two levels of information, two levels of interaction."

**Ive**: "The placeholder-to-portrait transition is clean. The card doesn't change shape or layout — only the content of the image area changes. Consistency of form."

**Jobs**: "This is the one. A character card should look like a character. Not a form. Not a spec sheet. A face and a name. That's how you know a person."

**Verdict**: Strong. Clean separation of recognition (card) from working detail (sheet). Scales well. Handles the pre/post render transition gracefully. But — the text attributes are buried in the detail view. Power users who care about the description have to tap into every character to see it.

---

### Approach C: "The Split Card" — Image and Text Side by Side

**Metaphor**: An ID badge or trading card. Image on the left, key attributes on the right.

```
PRE-RENDER:

+---------------------------+
|  +---------+  Kael        |
|  |         |  Warrior-Poet|
|  |  [?]    |  Era: Ancient|
|  |         |  Stoic       |
|  +---------+  [Render]    |
+---------------------------+

POST-RENDER:

+---------------------------+
|  +---------+  Kael        |
|  |[portrait|  Warrior-Poet|
|  | image]  |  Era: Ancient|
|  |         |  Stoic       |
|  +---------+  v1          |
+---------------------------+
```

Both the image and key attributes are always visible. The card is wider (landscape orientation in the rail) or the rail becomes a vertical list instead of horizontal scroll.

**Norman**: "This solves the 'both at once' problem. You see the face AND the description. But on mobile, this card is either too wide for a horizontal rail or too tall for a vertical list. The constraint is physics, not design."

**Ive**: "It's information-dense. Dense is not the same as complex, but it risks feeling clinical. This is a medical record, not a character portrait."

**Jobs**: "Too much. Pick one thing to show well. Don't try to show everything at once."

**Verdict**: Works on desktop. Doesn't fit mobile rails. The landscape format breaks the card pattern established for the rail. Could work as the detail view layout, but not as the card-in-rail.

---

### Approach D: "The Evolving Card" — Shape Changes With State

**Metaphor**: The card itself evolves. It starts as a text card (compact, attribute-focused). When a render arrives, it transforms into an image card (taller, portrait-focused). The card's physical form reflects its creative state.

```
STAGE 1 — Text only (just extracted):

+------------------+
|  Kael            |
|  ──────          |
|  Warrior-Poet    |
|  Ancient era     |
|  Stoic, poetic   |
|                  |
|  [Render ->]     |
+------------------+
   ~120px wide

STAGE 2 — Rendering:

+------------------+
|  +-----------+   |
|  | [shimmer] |   |
|  |  loading  |   |
|  +-----------+   |
|  Kael            |
|  Generating...   |
+------------------+

STAGE 3 — Rendered:

+------------------+
|  +-----------+   |
|  |           |   |
|  | [portrait]|   |
|  |           |   |
|  +-----------+   |
|  Kael            |
|  v1              |
+------------------+
```

The card starts as a compact text block and morphs into a portrait card when the render arrives. The transformation is animated — the text collapses upward as the image area expands downward.

**Norman**: "The shape change communicates state. A text card means 'this character is defined but not visualized.' A portrait card means 'this character has a face.' The form carries meaning. But — shape changes in a rail cause layout shifts, which are disorienting."

**Ive**: "The metamorphosis is beautiful in concept. But if the rail has 5 characters and they're all at different stages, you get a ragged rail with cards of different heights. That's visual chaos."

**Jobs**: "The idea is right. The execution needs discipline. The cards should be the same size. Put the evolution inside the fixed frame."

**Verdict**: The evolution concept is sound but the card dimensions must stay fixed. Combine with Approach B — fixed card frame, evolving content within it. This is the synthesis.

---

### Approach E: "The Layered Card" — Z-Axis Realized

**Metaphor**: The card has literal depth. The text layer sits behind the image layer. You can "peel back" the image to see the text underneath, or the card shows a subtle visual treatment that suggests depth.

```
RESTING STATE (render exists):

+------------------+
|  +-----------+   |
|  |           |   |
|  | [portrait]|   |
|  |       [≡] |   |  <- subtle icon: "there's text behind this"
|  +-----------+   |
|  Kael            |
|  v1              |
+------------------+

LONG-PRESS or TAP [≡]:
Image slides up to reveal attributes behind it:

+------------------+
|  +-----------+ ↑ |
|  | [portrait]| ↑ |  <- image lifts, partially visible at top
|  +-----------+ ↑ |
|  Kael            |
|  Warrior-Poet    |
|  Era: Ancient    |
|  Stoic, poetic   |
|  v1  [↓ image]   |
+------------------+
```

The image literally sits on top of the text, as a layer. The Z-axis metaphor is made physical. The text is always there — the image is a projection laid on top.

**Norman**: "This is conceptually correct — the image IS a projection of the text. The layering makes the relationship visible. But the gesture (long-press or special icon) has low discoverability. And the half-revealed state is awkward — neither fully image nor fully text."

**Ive**: "I like the idea that the image is a surface over deeper data. But the interaction of sliding one over the other feels like a trick, not a tool. It works once for delight, then becomes friction."

**Jobs**: "Too clever. Don't make people peel things apart. If they want to see both, show both. In the detail view."

**Verdict**: The conceptual model (image as projection of text) is exactly right for the Z-axis thinking. But the interaction on the card itself is too clever. Save this mental model for the detail view, where there's room to show both layers properly.

---

## Part 2: Our Recommendation — The Synthesis

None of the five approaches alone is complete. The answer is a combination:

### The Card (in the rail): Approach B + D synthesis

A fixed-size card that shows the **current best representation** of the character:

```
PRE-RENDER:                          POST-RENDER:

+------------------+                 +------------------+
|  +------------+  |                 |  +------------+  |
|  |            |  |                 |  |            |  |
|  |  monogram  |  |                 |  | [portrait] |  |
|  |    "K"     |  |                 |  |            |  |
|  |            |  |                 |  +------------+  |
|  +------------+  |                 |  Kael            |
|  Kael            |                 |  Warrior-Poet    |
|  Warrior-Poet    |                 |  o *o*  v2       |
|  [Render ->]     |                 +------------------+
+------------------+
```

**Rules**:
1. Card is always the same dimensions (fixed aspect ratio in the rail)
2. Pre-render: monogram/initial in the image area + name + one key trait below. A "Render" action.
3. Post-render: portrait fills the image area. Name + trait below. Variation dots if >1 version.
4. The card is a **recognition object** — just enough to identify who this is. Not a data sheet.

### The Detail View (bottom sheet / side panel): Approach E's mental model

This is where the dual nature is fully expressed. The detail view has **two zones**:

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                            |
|  Warrior-Poet of Vereth          |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |    [portrait image]        |  |    <- THE RENDER
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  [< prev]  o *o*  [next >]      |
|            v2 of 2               |
|                                  |
|  ┌ Description ──────────────┐   |
|  │ Warrior-poet of the old   │   |    <- THE TEXT
|  │ kingdom. Once commanded   │   |
|  │ the Southern Verse Guard. │   |
|  └───────────────────────────┘   |
|                                  |
|  ┌ Attributes ───────────────┐   |
|  │ Role       Protagonist    │   |
|  │ Era        Ancient        │   |
|  │ Form       Tall, lean     │   |
|  │ Palette    Storm grey     │   |
|  │ Markers    Scar, blade    │   |
|  │ Demeanor   Stoic, poetic  │   |
|  └───────────────────────────┘   |
|                                  |
|  ┌ References ───────────────┐   |
|  │ [photo] [photo] [+ Add]  │   |
|  └───────────────────────────┘   |
|                                  |
|  +----------------------------+  |
|  | How should Kael change?    |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
+----------------------------------+
```

The detail view is a scroll. Image at top (the render). Attributes below (the text). References below that. Refine prompt pinned at bottom. **Both layers are visible simultaneously, in their natural order: the visual projection on top, the underlying description below.**

This is the Z-axis made spatial: **image is literally above text because image is a projection of text.** You look at the image first (the surface). You scroll down to see the deeper layers (the attributes, the references). Depth is mapped to scroll position.

---

## Part 3: The Transition Moment — When the Render Arrives

This is the most important micro-interaction in the character flow. The character just got a face. How does the UI celebrate this?

### Option 1: "The Reveal" — Subtle

The monogram in the card fades out, the portrait fades in. The card doesn't change size or position. The rail stays still. The only thing that changes is the image area content.

**Timing**: Fade over 400ms, slight scale-up from 0.95 to 1.0 on the portrait.

**Feel**: Calm. Professional. "Of course this happened."

### Option 2: "The Emergence" — Medium

The card's image area shimmers during generation (like a loading skeleton). When the portrait arrives, the shimmer resolves into the image — like a Polaroid developing. The card gains a subtle border-glow for 1.5 seconds to draw the eye.

**Timing**: Shimmer resolves over 600ms. Glow fades over 1500ms.

**Feel**: Satisfying. "Something came to life."

### Option 3: "The Flip" — Dramatic

The entire card does a 3D flip (like Approach A's card flip), revealing the portrait side. The card flips from text-face to image-face.

**Timing**: Flip takes 500ms with slight overshoot (spring physics).

**Feel**: Theatrical. "Ta-da." But only works once. After that, the card is always image-first.

### Recommendation: Option 2 (The Emergence)

The shimmer-to-portrait resolution is the right amount of ceremony. It says "this was made for you" without demanding attention. And it reuses the shimmer/skeleton pattern you already have in ArtifactCard.

---

## Part 4: The Character Section — Three Layout Approaches

The character section sits below the story in the spine. It contains all characters. How are they arranged?

### Layout 1: Horizontal Rail (The Netflix)

```
CHARACTERS                    [+ Add]
+--------+ +--------+ +--------+ +----+
| [Kael] | | [Lyra] | | [Maren]| | +  |
|        | |        | |     >  | |    |
+--------+ +--------+ +--------+ +----+
<--- horizontal scroll --->
```

Characters scroll horizontally. This is the approach from the Timeline River exploration.

**Pros**: Compact vertical footprint. Familiar. Shows count at a glance (visual density of the rail).
**Cons**: Characters are hidden off-screen. You must scroll to see them all. On desktop, this pattern feels less natural.

### Layout 2: Wrapping Grid (The Gallery)

```
CHARACTERS                    [+ Add]
+--------+ +--------+ +--------+
| [Kael] | | [Lyra] | | [Maren]|
|        | |        | |        |
+--------+ +--------+ +--------+
+--------+ +--------+
| [Thane]| | [Eira] |
|        | |        |
+--------+ +--------+
```

Characters wrap into a grid. On mobile: 2-3 per row. On desktop: 4-6 per row.

**Pros**: All characters visible at once (no scrolling to discover). The grid is the natural layout for a "cast of characters."
**Cons**: Takes more vertical space. Many characters push scenes further down the page.

### Layout 3: Adaptive (Rail becomes Grid at threshold)

```
1-4 characters: Horizontal rail
5+ characters: Wrapping grid (with "Show all" if >8)
```

This is a responsive behavior within the section itself. Small casts get the compact rail. Large casts get the gallery. The section adapts to the content.

**Pros**: Best of both worlds.
**Cons**: The layout change at the threshold could be jarring. But if the user is adding characters one at a time, they cross the threshold during a natural pause.

### Layout 4: The Focused Rail (Our Recommendation)

A horizontal rail, but with a twist: the rail cards are bigger than typical Netflix thumbnails. They're portrait-sized. On mobile, you see ~2.3 cards (the ".3" creates the peek that signals scrollability). On desktop, you see all of them in a row that wraps.

```
MOBILE:
CHARACTERS                        [+ Add]
+----------+ +----------+ +-----
|  +-----+ | |  +-----+ | |  +--
|  |     | | |  |     | | |  |
|  | img | | |  | img | | |  | i
|  |     | | |  |     | | |  |
|  +-----+ | |  +-----+ | |  +--
|  Kael    | |  Lyra    | |  Ma>
|  Warrior | |  Oracle  | |
|  o *o*   | |  v1      | |
+----------+ +----------+ +-----
<----- scroll ----->

DESKTOP:
CHARACTERS                                              [+ Add]
+----------+ +----------+ +----------+ +----------+ +---------+
|  +-----+ | |  +-----+ | |  +-----+ | |  +-----+ | |  [+]   |
|  |     | | |  |     | | |  |     | | |  |     | | |        |
|  | img | | |  | img | | |  | img | | |  | img | | |  Add   |
|  |     | | |  |     | | |  |     | | |  |     | | | Char.  |
|  +-----+ | |  +-----+ | |  +-----+ | |  +-----+ | |        |
|  Kael    | |  Lyra    | |  Maren   | |  Thane   | +---------+
|  Warrior | |  Oracle  | |  Merchant| |  Captain |
|  o *o*   | |  v1      | |  v1      | |  o o     |
+----------+ +----------+ +----------+ +----------+
```

**Why this works**: The cards are large enough to be meaningful (the portrait is visible, the name is readable), the peek on mobile signals "swipe for more," and on desktop they simply flow into a row or wrap. The same component, two contexts.

---

## Part 5: The Detail View — Refinement of Attributes vs Image

This is the crux of the "two levels" problem. When the user taps into a character, they need to be able to refine two different things:

1. **The description/attributes** — "Make him older," "Change her role to antagonist"
2. **The rendered image** — "More weathered," "Different angle," "Make the armor more ornate"

These are different operations with different targets. Changing attributes may stale the image. Changing the image doesn't change the attributes.

### Approach 1: "Single Refine, AI Figures It Out"

One prompt input. The AI determines whether the user is refining the description or the image based on the content of the prompt.

"Make him older" → updates attributes + marks image stale
"Make the armor more ornate in the image" → regenerates image only
"He should be a villain, not a hero" → updates attributes + marks image stale

**Pros**: Simplest UX. One input, one action.
**Cons**: Ambiguity. "Make him scarier" — does that change the description or the image? Both? The AI has to guess. The user loses control.

### Approach 2: "Segmented Refine" — Two Targets, One Input

The refine input has a target selector:

```
+-----------------------------------+
|  Refining: [Description v] [Image]|
|  +-------------------------------+|
|  | Make him older, weathered     ||
|  |                [Generate ->]  ||
|  +-------------------------------+|
+-----------------------------------+
```

A toggle or segmented control above the prompt indicates what you're refining. Default is "Description" if no render exists, "Image" if one does.

**Pros**: Explicit. No ambiguity. The user knows what they're changing.
**Cons**: An extra choice. Beginners don't know the difference or don't care.

### Approach 3: "The ArtifactCard Handles It" — Refine is Context-Aware

The ArtifactCard already has `onRefine` and `enableAttachments`. The character detail view is composed of **two ArtifactCards stacked vertically**:

```
+----------------------------------+
|  Kael                            |
+----------------------------------+
|                                  |
|  [ArtifactCard: Portrait]        |
|  +----------------------------+  |
|  |    [portrait image]        |  |
|  +----------------------------+  |
|  [Refine] <- refines the image   |
|                                  |
|  [ArtifactCard: Description]     |
|  +----------------------------+  |
|  | Role: Protagonist          |  |
|  | Era: Ancient               |  |
|  | Visual Form: Tall, lean... |  |
|  | Demeanor: Stoic, poetic    |  |
|  +----------------------------+  |
|  [Refine] <- refines attributes  |
|                                  |
+----------------------------------+
```

Each artifact has its own Refine. The portrait card refines the image (and accepts photo uploads as references). The description card refines the attributes.

**Pros**: Reuses ArtifactCard. No new concepts. Each artifact is independently refinable. Clear which thing you're changing.
**Cons**: Two refine buttons in one view. Slightly more complex than a single prompt.

### Approach 4: "Smart Default, Explicit Override" — The Synthesis

One refine input at the bottom of the detail view (like the current exploration wireframes show). The default target is **intelligent**:

- If no render exists → refine targets the description
- If render exists → refine targets the image (because that's what the user is looking at)
- A small toggle allows explicit override: `Refining: [Image] | Description`

The toggle is subtle — small text, not a button group. Beginners ignore it. Pros use it.

```
PRE-RENDER detail view:

+----------------------------------+
|  Kael                            |
|  +----------------------------+  |
|  |    [ monogram "K" ]        |  |
|  +----------------------------+  |
|  Role: Protagonist               |
|  Era: Ancient                    |
|  ...                             |
|                                  |
|  +----------------------------+  |
|  | Describe Kael further...   |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
|  Refining: Description           |
+----------------------------------+

POST-RENDER detail view:

+----------------------------------+
|  Kael                            |
|  +----------------------------+  |
|  |    [portrait image]        |  |
|  +----------------------------+  |
|  [< v1]  o *o*  [v2 >]          |
|                                  |
|  Role: Protagonist               |
|  Era: Ancient                    |
|  ...                             |
|                                  |
|  +----------------------------+  |
|  | How should Kael look?      |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
|  Refining: Image | Description   |
+----------------------------------+
```

**Norman**: "The smart default reduces decision cost. The toggle preserves control. This is the principle of 'recognition over recall' — the system remembers the likely target, the user corrects when needed."

**Ive**: "The placeholder text shifts to match the target. 'Describe Kael further...' vs 'How should Kael look?' — the language is the affordance."

**Jobs**: "One input. Smart default. Tiny escape hatch. Ship it."

### Our Recommendation: Approach 4 (Smart Default)

Single refine input. Smart default target. Small text toggle for explicit override. The ArtifactCard's `onRefine` callback receives the payload plus a `target: 'description' | 'render'` field. The parent decides what to do with it.

This means the ArtifactCard doesn't need to know about the dual nature — it just sends the payload. The Character detail view (the parent) adds the target based on the toggle state.

---

## Part 6: Reference Images — Where Do They Live?

Users want to upload photos of themselves or friends to make characters look like real people. This is a core use case: personal stories.

References are **inputs to the render**, not artifacts themselves. They influence the image but are not the image.

### In the Detail View:

```
+----------------------------------+
|  Kael                            |
|  +----------------------------+  |
|  |    [portrait image]        |  |
|  +----------------------------+  |
|                                  |
|  --- References ----             |
|  +------+ +------+ +------+     |
|  |[photo|  |[photo|  | [+]  |     |
|  | ref1] |  | ref2] |  | Add |     |
|  +------+ +------+ +------+     |
|                                  |
|  --- Attributes ----             |
|  Role: Protagonist               |
|  ...                             |
+----------------------------------+
```

References appear as a small thumbnail strip between the portrait and the attributes. They're visually subordinate — smaller thumbnails, not full-size. The [+] button opens the file picker (or camera on mobile).

References can also be added via the RefineInput's attachment feature. When the user attaches a photo while refining the image, they can choose to save it as a reference or use it as a one-time input.

### In the Card (rail view):

References are NOT shown in the card. They're a detail-level concern. The card shows only the result (portrait or monogram).

### The Upload Flow:

1. User taps [+ Add] in the References section, OR attaches a photo in the refine input
2. Photo uploads and appears as a thumbnail
3. Next time the user renders/refines the portrait, the references are sent as input
4. The AI uses the references to guide the generation

This keeps the reference flow inside the existing ArtifactCard refinement loop. The RefineInput already supports attachments (`enableAttachments`). The difference is that for character renders, attachments can be **persisted as references** rather than being one-time inputs.

---

## Part 7: The Pre-Render State — Making Text Not Feel Like a Wall

The core anxiety: "characters start as structured text, and text on screen feels like a wall." Here are strategies to make the text-only state feel visual, alive, and not like a form.

### Strategy 1: The Monogram Card

Pre-render cards show a large styled initial/monogram instead of a blank space:

```
+------------------+
|  +------------+  |
|  |            |  |
|  |     K      |  |  <- Large letter, styled with
|  |            |  |     a color derived from the
|  |            |  |     character's palette attribute
|  +------------+  |
|  Kael            |
|  Warrior-Poet    |
+------------------+
```

The monogram's background color is derived from the `colorPalette` attribute. "Storm grey and silver" → a cool grey gradient. "Crimson and gold" → a warm red tone. The character's essence is expressed chromatically even before the portrait exists.

### Strategy 2: The Trait Pills

Instead of showing attributes as key-value text, show them as pills/chips:

```
+------------------+
|  +------------+  |
|  |     K      |  |
|  +------------+  |
|  Kael            |
|  [Warrior] [Poet]|
|  [Ancient] [Stoic|
+------------------+
```

Traits as chips feel lighter than "Role: Protagonist, Era: Ancient." They scan faster. They feel like tags, not a database record.

### Strategy 3: The Brief-First Card

Show only the `brief` (the one-line description) on the card, not the full attribute set:

```
+------------------+
|  +------------+  |
|  |     K      |  |
|  +------------+  |
|  Kael            |
|  "A warrior-poet |
|   who carries a  |
|   humming blade" |
+------------------+
```

The brief is the most human-readable attribute. It reads like a character introduction, not a spec sheet. Full attributes live in the detail view.

### Our Recommendation: Strategy 1 + 3 (Monogram + Brief)

The pre-render card shows: monogram (with palette-derived color), name, and brief. That's it. No key-value pairs. No attribute lists. The card reads like a character introduction in a novel, not a database row.

```
PRE-RENDER CARD:

+------------------+
|  +------------+  |
|  |            |  |
|  |     K      |  |  <- palette-derived color
|  |            |  |
|  +------------+  |
|  Kael            |
|  A warrior-poet  |
|  who carries a   |
|  humming blade   |
+------------------+

POST-RENDER CARD:

+------------------+
|  +------------+  |
|  |            |  |
|  | [portrait] |  |
|  |            |  |
|  +------------+  |
|  Kael            |
|  Warrior-Poet    |
|  o *o*  v2       |
+------------------+
```

The card evolved from "literary introduction" to "visual portrait." Both feel appropriate for their state. Neither feels like a wall of text or an empty shell.

---

## Part 8: Putting It All Together — The Character Lifecycle

### Stage 1: Characters Extracted (text only)

```
STORY                           v1
+------------------------------+
| "Rain hammered the cracked   |
|  cobblestones of Vereth..."  |
| [Read more v]                |
+------------------------------+
[Refine]

CHARACTERS
+----------+ +----------+ +-----
|  +-----+ | |  +-----+ | |  +--
|  |     | | |  |     | | |  |
|  |  K  | | |  |  L  | | |  | M
|  |     | | |  |     | | |  |
|  +-----+ | |  +-----+ | |  +--
|  Kael    | |  Lyra    | |  Ma>
|  A war-  | |  The     | |
|  rior... | |  blind...| |
+----------+ +----------+ +-----

+------------------------------+
| Your characters need faces.  |
|                              |
| [Render All ->]              |
| or tap a character to refine |
| their description first      |
+------------------------------+
```

Cards show monograms with palette colors. Briefs below. The suggestion nudges toward rendering but doesn't force it. The user can tap any card to refine its description first.

### Stage 2: User Taps Kael (detail view, pre-render)

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                            |
|  A warrior-poet who carries      |
|  a blade that hums in moonlight  |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |        [ K ]               |  |  <- large monogram
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  --- Attributes ---              |
|  Role       Protagonist          |
|  Era        Ancient              |
|  Form       Tall, lean, scarred  |
|  Palette    Storm grey, silver   |
|  Markers    Scar across jaw,     |
|             humming blade        |
|  Demeanor   Stoic, poetic        |
|                                  |
|  --- References ---              |
|  [+ Add reference photo]         |
|                                  |
|  +----------------------------+  |
|  | Describe Kael further...   |  |
|  | [attach] [mic] [send ->]   |  |
|  +----------------------------+  |
|  Refining: Description           |
+----------------------------------+
```

The user can:
- Upload reference photos (themselves, a friend)
- Refine the description ("make him older, add more scars")
- Or just close and tap "Render All" back in the main view

### Stage 3: Render is Generating

```
CHARACTERS
+----------+ +----------+ +-----
|  +-----+ | |  +-----+ | |
|  |shim-| | |  |     | | |
|  |mer  | | |  |  L  | | |
|  |     | | |  |     | | |
|  +-----+ | |  +-----+ | |
|  Kael    | |  Lyra    | |
|  Generat.| |  A blind | |
+----------+ +----------+ +-----
```

The card that's generating shows a shimmer in the image area. The name stays. Other cards are unchanged.

### Stage 4: Renders Arrive

```
CHARACTERS
+----------+ +----------+ +-----
|  +-----+ | |  +-----+ | |
|  |     | | |  |     | | |
|  | img | | |  | img | | |  im
|  |     | | |  |     | | |
|  +-----+ | |  +-----+ | |
|  Kael    | |  Lyra    | |  Ma
|  Warrior | |  Oracle  | |
|  v1      | |  v1      | |
+----------+ +----------+ +-----
```

Portraits emerge from shimmers (Option 2: The Emergence from Part 3). Cards now show portraits, names, and version indicators. The brief text is replaced by the short role label ("Warrior-Poet" → "Warrior" for space).

### Stage 5: User Refines Kael's Image (detail view, post-render)

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                            |
|  Warrior-Poet of Vereth          |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |    [portrait image v1]     |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  *o*  v1 of 1                    |
|                                  |
|  --- Attributes ---              |
|  Role       Protagonist          |
|  Era        Ancient              |
|  Form       Tall, lean, scarred  |
|  Palette    Storm grey, silver   |
|  Markers    Scar, humming blade  |
|  Demeanor   Stoic, poetic        |
|                                  |
|  --- References ---              |
|  [photo1] [photo2] [+ Add]      |
|                                  |
|  +----------------------------+  |
|  | How should Kael look?      |  |
|  | "More weathered, older,    |  |
|  |  battle-worn armor"        |  |
|  |  [attach] [mic] [send ->]  |  |
|  +----------------------------+  |
|  Refining: Image | Description   |
+----------------------------------+
```

The user types a refinement. A new image (v2) generates. The portrait updates. Variation dots appear (now 2). The user swipes between v1 and v2 in the image area.

---

## Part 9: Desktop Adaptation

On desktop (>768px), the bottom sheet becomes a side panel. The main canvas (spine + rails) remains visible on the left. The character detail occupies the right panel.

```
+--------------------------------------+--------------------+
|                                      |                    |
|  STORY                         v1    |  Kael              |
|  +------------------------------+    |  Warrior-Poet      |
|  | "Rain hammered the cracked   |    |                    |
|  | cobblestones of Vereth..."   |    |  +------------+    |
|  +------------------------------+    |  |            |    |
|  [Refine]                            |  | [portrait] |    |
|                                      |  |            |    |
|  CHARACTERS                          |  +------------+    |
|  [*Kael*] [Lyra] [Maren] [+]       |                    |
|                                      |  o *o*  v2 of 2   |
|  SCENES                              |                    |
|  [coming soon]                       |  Attributes:       |
|                                      |  Role: Protagonist |
|                                      |  Era: Ancient      |
|                                      |  ...               |
|                                      |                    |
|                                      |  References:       |
|                                      |  [img] [img] [+]   |
|                                      |                    |
|                                      |  [______________]  |
|                                      |  Refining: Image   |
|                                      |  [Generate ->]     |
+--------------------------------------+--------------------+
```

The selected character card in the rail gets a highlight. The side panel shows full detail. The user can see their entire project while examining one character. Click another character card → the side panel updates. No navigation, just selection.

---

## Part 10: How This Maps to Existing Code

### What already works:
- **ArtifactCard** is the shell. It handles title, content slot, refine input, collapsible content, attachments. Characters will use ArtifactCard for both the description artifact and the portrait artifact.
- **RefineInput** already supports text, voice, and image attachments. Character portrait refinement will use this directly.
- **ContentCard** handles overflow and gradient-fade collapse. Character attributes can use this.
- **StoryWorkspace** already has the spine layout with `max-w-3xl mx-auto`. The character section slots in below the story ArtifactCard.

### What needs to be built:
1. **CharacterCard** (new) — The card component for the rail. Shows monogram/portrait + name + trait. Tap opens detail.
2. **CharacterDetail** (new) — The bottom sheet / side panel content. Portrait, attributes, references, refine input with target toggle.
3. **CharacterSection** (new) — The rail/section in the spine. Contains the character cards + suggestion nudge + "Render All" action.
4. **Character data hooks** — useExtractCharacters, useRenderCharacter, useCharacterDetail, etc.
5. **Monogram component** — Generates a styled initial with a color derived from character attributes.

### What ArtifactCard needs (if anything):
Probably nothing. The CharacterDetail view composes ArtifactCard instances for the portrait and description sections. ArtifactCard doesn't need to know about characters specifically. It's just a shell that shows content and offers refinement.

---

## Part 11: Open Questions for the Client

1. **Render all vs render individually?** The suggestion nudge says "Render All." But should users also be able to render individual characters from the rail (without opening the detail view)? Recommendation: Both. "Render All" on the section, individual render in the detail view.

2. **Attribute schema flexibility.** You said the schema will change. Should the detail view render attributes dynamically (iterate over object keys) or should we design for specific known fields? Recommendation: Dynamic. The `formatKey` function from the old CharacterCard already does `camelCase → Title Case`. Render whatever the object contains.

3. **When does the suggestion nudge appear?** Immediately after extraction? Or after a short delay to let the user absorb the results? Recommendation: 1.5-second delay (per the interaction patterns doc). Let the user see their characters before pushing them forward.

4. **Variation scope.** Do description variations and image variations share one version timeline, or are they independent? E.g., if you refine the description (creating desc v2), does that create a new "character version" or just a new "description version"? Recommendation: Independent. Description has its own version track. Image has its own version track. They're linked by dependency (description change stales the image) but not by version number.

5. **Should the card in the rail show variation dots for description variations, image variations, or both?** Recommendation: Image variations only (once renders exist). Pre-render, no dots (there's nothing visual to compare). The description variation history lives in the detail view only.

---

*"Simplicity is the ultimate sophistication." — Leonardo da Vinci (and the Apple marketing team)*

*This document is a starting point. The wireframes describe intent, not pixels. The approaches describe trade-offs, not mandates. The recommendation is our strongest opinion, held loosely.*
