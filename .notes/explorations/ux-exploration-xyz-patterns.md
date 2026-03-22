# UX Exploration: The XYZ Creative Space

**Date**: 2026-02-23  
**Context**: Designing the spatial UI model for a generative narrative media engine  
**Design Principles**: Simplicity. Mobile-first. Progressive disclosure. Physics-grounded metaphor.

---

## Part 1: The Problem, Clearly Stated

We have a creative engine that produces narrative media. The user's creative work has three dimensions:

1. **Flow (Y-axis)**: A vertical sequence of creative artifacts -- story, characters, scenes, renders. This is the spine. It grows downward. It could be 4 things or 40.

2. **Variation (X-axis)**: Any artifact can have alternatives. A character description might have 3 versions. A rendered image might have 5 attempts. Variations grow horizontally.

3. **Projection/Layers (Z-axis)**: The same narrative content can be projected into different media -- comic panels, audio, animation. Layers go into depth. (Future, but the architecture must accommodate it.)

The old stepper approach (comic-builder) failed because it imposed a rigid sequential pipeline on inherently fluid creative work. The new story feature's two-panel split failed because it doesn't scale beyond a single phase -- it has no structural answer for "what comes after the story?"

We need a UI that:
- Feels like one continuous creative workspace, not a wizard
- Works beautifully on a phone (90% of users)
- Makes variation creation feel effortless, not bureaucratic
- Grows from simple to powerful without redesign
- Makes dependencies visible without making them overwhelming

---

## Part 2: First Principles

### Principle 1: The Document Metaphor
People understand documents. A long vertical scroll is the most natural digital container. Every social feed, every chat app, every article -- vertical scroll is literacy-level familiar. **The Y-axis is free -- we already know how to scroll.**

### Principle 2: The Physics of Attention
On mobile, your thumb sweeps vertically with ease and horizontally with intention. Vertical is browsing. Horizontal is choosing. This maps perfectly: **scroll the flow, swipe the variations.**

### Principle 3: Progressive Disclosure via Depth
You don't show everything. You show the current best version of each artifact in the flow. Variations exist but are revealed on demand. Layers exist but are revealed when the user is ready. **The surface is simple. The depth is powerful.**

### Principle 4: Dependency as Gravity
In the vertical flow, things above influence things below. If you change a character description, everything below it (scenes that use that character, renders of those scenes) is affected. **Gravity pulls influence downward.** This is intuitive -- cause above, effect below.

### Principle 5: The Studio, Not the Wizard
A wizard says "do this, then this, then this." A studio says "here is your workspace -- everything is here, work on what matters." **The user should be able to glance at their entire creative state and touch any part of it.**

---

## Part 3: The Anatomy of a Node

Before exploring layout patterns, we need to define what a single "thing" in the flow looks like. Every artifact in the flow is a **Node**. A node has:

```
+------------------------------------------+
|  [Type Label]            [Status Badge]  |
|                                          |
|  [Content Area]                          |
|  The actual artifact -- text, image,     |
|  or a summary of structured data.        |
|                                          |
|  [Variation Indicator]    [Action Area]  |
|  "v2 of 3"  [< >]        [Refine]       |
+------------------------------------------+
```

- **Type Label**: What this is (Story, Character, Scene, Panel)
- **Status Badge**: Current state (generated, stale, generating...)
- **Content Area**: The actual creative output
- **Variation Indicator**: Which version you're looking at, out of how many
- **Action Area**: What you can do (refine, regenerate, expand)

This is the atom. Everything below is about how atoms are arranged.

---

## Part 4: Three Options

---

### Option A: The Vertical River

**Metaphor**: A river flowing downward. Each node is a stone in the river. The river is the creative flow. Variations are eddies -- side currents that branch off and rejoin.

#### Layout

```
Phone Screen (375px)
+----------------------------------+
|  [Project Name]           [...]  |
+----------------------------------+
|                                  |
|  +----- STORY ---------------+  |
|  | "In the ancient city..."  |  |
|  | ...                       |  |
|  |            v1 of 2  [< >] |  |
|  |                  [Refine] |  |
|  +---------------------------+  |
|         |                        |
|         v  (flow connector)      |
|  +----- CHARACTER: Kael -----+  |
|  | Warrior-poet of the...    |  |
|  |   [portrait image]        |  |
|  |            v1 of 1  [< >] |  |
|  |                  [Refine] |  |
|  +---------------------------+  |
|         |                        |
|         v                        |
|  +----- CHARACTER: Lyra -----+  |
|  | The blind oracle who...   |  |
|  |   [portrait image]        |  |
|  |            v3 of 3  [< >] |  |
|  |                  [Refine] |  |
|  +---------------------------+  |
|         |                        |
|         v                        |
|  +----- SCENE 1 -------------+  |
|  | The market square at dawn |  |
|  |   [comic panel]           |  |
|  |            v1 of 1  [< >] |  |
|  |                  [Refine] |  |
|  +---------------------------+  |
|         |                        |
|         v                        |
|  +----- SCENE 2 -------------+  |
|  | ...                       |  |
|                                  |
+----------------------------------+
```

#### Variation Navigation

Variations are navigated by **swiping horizontally on a node** or tapping the `[< >]` arrows. Think of it like swiping between photos in a gallery. The node content slides left/right to reveal alternate versions.

```
Swipe left on "CHARACTER: Kael" node:

  +---------------------------+
  | CHARACTER: Kael           |
  |                           |
  | [v1: current] -> [v2]    |
  |  <-- swipe animation -->  |
  +---------------------------+
```

The variation indicator updates: `v2 of 2`. Small dots below the content (like iOS page dots) show position.

#### Creating a New Variation

When you tap **[Refine]**, a prompt sheet slides up from the bottom of the screen (mobile) or appears as an inline input field below the node (desktop):

```
+----------------------------------+
|  +----- CHARACTER: Kael -----+  |
|  | Warrior-poet of the...    |  |
|  +---------------------------+  |
|                                  |
|  +-- REFINE PROMPT -----------+  |
|  | "Make him older, more      |  |
|  |  weathered, with a scar"   |  |
|  |              [Generate ->] |  |
|  +---------------------------+  |
```

The result creates a new variation (v2) and auto-swipes to it. The previous version is preserved.

#### Stale State

When a node above changes (e.g., story is regenerated), dependent nodes below get a subtle visual treatment:

```
  +----- CHARACTER: Kael -----+
  | [STALE - story changed]   |  <-- amber banner
  | Warrior-poet of the...    |
  |            v1 of 2  [< >] |
  |     [Refresh] [Keep]      |  <-- explicit choice
  +---------------------------+
```

#### Strengths
- Extremely simple mental model: scroll down = see more of your project
- Swiping for variations is a gesture people already know (photo galleries)
- Works perfectly on mobile -- the entire width is the node
- Dependency direction is visually obvious (top to bottom)
- Adding new node types to the flow is trivial -- just append

#### Weaknesses
- For many characters (say 10), the flow gets very long -- you're scrolling past characters to get to scenes
- No way to see multiple variations side-by-side without a separate comparison mode
- The flow implies sequence even where there isn't one (characters aren't really "in order")

#### When to Use This
Best when the project is small-to-medium (5-15 nodes) and the user primarily works top-to-bottom.

---

### Option B: The Spine and Ribs

**Metaphor**: A spine runs down the center. Each node type is a vertebra. Variations extend as ribs to the left and right. The spine is the "current best" path through the creative work.

#### Layout

```
Phone Screen (375px)
+----------------------------------+
|  [Project Name]           [...]  |
+----------------------------------+
|                                  |
|  STORY                           |
|  +---------------------------+   |
|  | "In the ancient city..."  |   |
|  +---------------------------+   |
|              |                   |
|  CHARACTERS  |                   |
|  +---------------------------+   |
|  | [Kael] [Lyra] [Maren] +2 |   |
|  +---------------------------+   |
|              |                   |
|  SCENES      |                   |
|  +---------------------------+   |
|  | Scene 1: Market Square    |   |
|  | Scene 2: The Betrayal     |   |
|  | Scene 3: The Climb        |   |
|  +---------------------------+   |
|              |                   |
|  RENDERS     |                   |
|  +---------------------------+   |
|  | [panel] [panel] [panel]   |   |
|  +---------------------------+   |
|                                  |
+----------------------------------+
```

This is the **collapsed view** -- each section is a summary card. **Tapping a section expands it** to reveal the full content of that layer:

```
Expanded CHARACTERS section:

+----------------------------------+
|  CHARACTERS              [^]     |
+----------------------------------+
|                                  |
|  +-- Kael --+  +-- Lyra --+     |
|  | [image]  |  | [image]  |     |
|  | warrior  |  | oracle   |     |
|  | v3 of 3  |  | v1 of 2  |     |
|  | [Refine] |  | [Refine] |     |
|  +----------+  +----------+     |
|                                  |
|  +-- Maren -+  +-- Thane -+     |
|  | [image]  |  | [image]  |     |
|  | merchant |  | captain  |     |
|  | v1 of 1  |  | v2 of 2  |     |
|  | [Refine] |  | [Refine] |     |
|  +----------+  +----------+     |
|                                  |
+----------------------------------+
```

Within an expanded section, individual items can be tapped to go into **detail view**, which is where variations become visible:

```
Detail View: Kael (full screen)

+----------------------------------+
|  [<- Back]  Kael          [...]  |
+----------------------------------+
|                                  |
|  +----- v3 (current) --------+  |
|  |                            |  |
|  |  [full portrait image]     |  |
|  |                            |  |
|  |  Warrior-poet of the old   |  |
|  |  kingdom. Carries a blade  |  |
|  |  that hums in moonlight... |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  [< v2]  o o *o*  [v3 >]        |  <-- pagination dots
|                                  |
|  +-- Prompt History ----------+  |
|  | v1: "extract characters"   |  |
|  | v2: "make him older"       |  |
|  | v3: "add the scar, keep    |  |
|  |      the poet aspect"      |  |
|  +----------------------------+  |
|                                  |
|  [Refine This Version]          |
|                                  |
+----------------------------------+
```

#### Creating Variations

From the detail view, tap **[Refine This Version]**. A bottom sheet slides up with the prompt input. Submitting creates a new variation and swipes to it.

Crucially: **the prompt history is visible**. You can see the chain of refinements that led to each version. This is the creative genealogy.

#### Stale State

In the collapsed view, an entire section gets a subtle indicator:

```
  CHARACTERS  [! 2 stale]
  +---------------------------+
  | [Kael] [Lyra] [Maren] +2 |
  +---------------------------+
```

Expanding the section shows which specific items are stale.

#### Strengths
- **Collapse/expand gives the "studio at a glance" view** -- you can see your entire project in one screen
- Scales much better for many items (10 characters don't push scenes off screen)
- Detail view for variations gives you space to see the full artifact and its history
- The section model maps cleanly to the simulation-engine ontology (World, Characters, Scenes, Projections)
- **Mobile-native**: collapse/expand is standard accordion behavior; detail view is standard drill-down

#### Weaknesses
- Three levels of navigation (collapsed sections -> expanded section -> detail view) adds cognitive overhead
- The "flow" feeling is less visceral -- sections feel more like a dashboard than a river
- Switching between detail views of related items (character + the scene they appear in) requires back-and-forth navigation

#### When to Use This
Best when the project is large (many characters, many scenes) and the user needs overview + drill-down.

---

### Option C: The Timeline River (Hybrid)

**Metaphor**: A river where the water level rises. Each "layer" of the creative flow is a horizontal band that spans the full width. Within each band, items scroll horizontally. The bands stack vertically. **The vertical axis is the flow type. The horizontal axis is the items within that type. Variation is depth within an item.**

This is the option that most closely mirrors the XYZ model:
- Y = flow layers (story, characters, scenes, renders)
- X = items within a layer + variations within an item  
- Z = projection type (future)

#### Layout

```
Phone Screen (375px)
+----------------------------------+
|  [Project Name]           [...]  |
+----------------------------------+
|                                  |
|  STORY                           |
|  +------------------------------+|
|  | "In the ancient city of      ||
|  | Vereth, where stone bridges  ||
|  | span chasms older than       ||
|  | memory..."                   ||
|  |                   [Refine]   ||
|  +------------------------------+|
|                                  |
|  CHARACTERS            [+ Add]  |
|  +--------+ +--------+ +------+ |
|  | [Kael] | | [Lyra] | | [Ma> | |
|  | v3     | | v1     | |      | |
|  +--------+ +--------+ +------+ |
|  <--- horizontal scroll --->     |
|                                  |
|  SCENES                [+ Add]  |
|  +--------+ +--------+ +------+ |
|  | Sc. 1  | | Sc. 2  | | Sc>  | |
|  | Market | | Betray | |      | |
|  +--------+ +--------+ +------+ |
|  <--- horizontal scroll --->     |
|                                  |
|  PANELS                          |
|  +--------+ +--------+ +------+ |
|  | [img]  | | [img]  | | [i>  | |
|  | Sc1-p1 | | Sc1-p2 | |      | |
|  +--------+ +--------+ +------+ |
|  <--- horizontal scroll --->     |
|                                  |
+----------------------------------+
```

Each band is a **horizontal scrolling rail**. Story is special -- it's a single wide card (or a few, if there are story variations). Characters, Scenes, and Panels are collections that scroll horizontally.

#### Tapping Into an Item

Tapping a character card, for example, opens a **bottom sheet** (on mobile) or **side panel** (on desktop) showing the full detail:

```
Bottom Sheet (slides up from bottom, 85% height):

+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                     [x]   |
|  Warrior-Poet                    |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |  [full portrait image]     |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  [< v2]  o o *o*  [>]           |
|                                  |
|  Description                     |
|  Warrior-poet of the old         |
|  kingdom. Carries a blade...     |
|                                  |
|  Traits                          |
|  [Stoic] [Poetic] [Scarred]     |
|                                  |
|  Appears in                      |
|  Scene 1, Scene 3, Scene 7      |
|                                  |
|  +----------------------------+  |
|  | Refine: "make the scar    |  |
|  | more prominent"           |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
|                                  |
+----------------------------------+
```

The bottom sheet is the **detail + variation + refinement** surface. Everything about a single item lives here. Swiping left/right in the image area cycles through variations.

The refinement prompt is **always visible at the bottom of the sheet** -- not hidden behind a button. This is key: **the invitation to refine is ever-present**. The lowest friction path to creating a variation.

#### Creating Variations

The prompt input at the bottom of every detail sheet. Type, submit, a new variation appears. The sheet stays open. You see the result immediately.

For items that don't need a detail sheet (like story text), the **[Refine]** button on the card itself opens an inline prompt:

```
  STORY
  +------------------------------+
  | "In the ancient city..."     |
  |                              |
  | +-- Refine ---------------+ |
  | | "Make the opening more   | |
  | |  dramatic, add weather"  | |
  | |            [Generate ->] | |
  | +--------------------------+ |
  +------------------------------+
```

#### Stale State in the Rails

When something upstream changes, downstream rails get a visual treatment:

```
  SCENES  [2 need refresh]   [Refresh All]
  +--------+ +--------+ +--------+
  | Sc. 1  | | Sc. 2  | | Sc. 3  |
  | [stale]| |  ok    | | [stale]|
  +--------+ +--------+ +--------+
```

Stale items have a subtle amber tint and a refresh icon. The section header shows a count and a batch refresh action.

#### Strengths
- **The overview is powerful**: you can see the entire project at a glance -- story, all characters, all scenes, all panels -- without expanding anything
- **Horizontal rails are extremely mobile-friendly** -- this is how Netflix, Spotify, App Store, and every major mobile app presents collections
- **The bottom sheet pattern is iOS/Android native** -- users already know how to interact with it
- **Refinement is always one tap away** -- no navigation required to start improving something
- **Scales gracefully**: 3 characters or 30 characters -- the rail just scrolls
- **The XYZ model is literally visible**: scroll vertically through flow layers, scroll horizontally through items, swipe through variations in the detail sheet

#### Weaknesses
- Horizontal scrolling hides items -- you can't see all characters at once without scrolling
- The bottom sheet is a modal layer -- while refining a character, you can't simultaneously see the scene that uses them
- The "flow" connection between layers is visual (vertical stacking) but not interactive -- you don't see the dependency arrows

#### When to Use This
Best for mobile-first design with moderate-to-large projects. This is the pattern that most naturally maps to existing mobile UX conventions.

---

## Part 5: Interaction Design Deep-Dive -- The Refinement Flow

This is the crux of the UX challenge. How does a user go from "I don't like this" to "generate me a better version"?

### The Hover Problem (Desktop) and the Touch Problem (Mobile)

On desktop, hovering over a node to reveal a prompt box is natural. On mobile, there is no hover. So we need a gesture vocabulary:

**Universal principle: Refine is always visible, never hidden behind hover.**

### Pattern: The Persistent Prompt

Every node, in every view, has a visible refinement affordance. It's not hidden. It's not behind a hover. It's a small, unobtrusive but always-present element.

On mobile, this is a small button or icon at the bottom-right of each node card. On desktop, it can be the same, or it can expand on hover to show the full prompt input.

```
Mobile card (compact):
+------------------------+
| CHARACTER: Kael        |
| [portrait thumbnail]   |
| v3 of 3    [Refine ->] |  <-- always visible
+------------------------+

Desktop card (hover state):
+----------------------------------+
| CHARACTER: Kael                  |
| [portrait]  Warrior-poet...     |
|                                  |
| +------------------------------+ |
| | "make him more intimidating" | |  <-- appears on hover
| |               [Generate ->]  | |
| +------------------------------+ |
+----------------------------------+
```

### Pattern: The Refine Sheet (Mobile)

On mobile, tapping [Refine] opens a bottom sheet that is **context-aware**:

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Refining: Kael (v3)            |
|                                  |
|  Current:                        |
|  "Warrior-poet of the old       |
|   kingdom..."                    |
|                                  |
|  Previous refinements:           |
|  v1 -> v2: "make him older"     |
|  v2 -> v3: "add the scar"      |
|                                  |
|  +----------------------------+  |
|  | Your refinement:           |  |
|  | "make his armor more       |  |
|  |  ornate, ceremonial"       |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
+----------------------------------+
```

The sheet shows:
1. What you're refining (with context)
2. How it got to this version (prompt lineage)
3. Your new instruction

This respects Don Norman's principle of **visibility**: the user can see the full context of their creative decision.

### Pattern: The Stale Cascade

When you refine a node, everything downstream is potentially affected. The UI must make this visible without being alarming.

```
User refines Story (v1 -> v2):

  STORY  [v2 - just generated]
  +------------------------------+
  | "In the war-torn city..."    |   <-- new version
  +------------------------------+
         |
         v
  CHARACTERS  [may need refresh]     <-- amber, not red
  +--------+ +--------+
  | Kael   | | Lyra   |
  | [!]    | | [!]    |              <-- subtle indicator
  +--------+ +--------+

  SCENES  [may need refresh]
  ...
```

The staleness indicator is **informational, not blocking**. The user can:
- Ignore it (keep working with existing versions)
- Refresh individual items
- Refresh an entire section
- Refresh everything downstream with one action

This is the "dependency awareness" from the simulation-engine doc, made tangible.

---

## Part 6: Desktop Adaptation

All three options above are described mobile-first. Here's how they adapt to desktop:

### Option A (Vertical River) on Desktop
The nodes get a max-width (say 720px) and center in the viewport. More content is visible per node. Hover reveals inline prompt fields. The experience is like a long-form editor (Notion, Google Docs).

### Option B (Spine and Ribs) on Desktop
The collapsed view becomes a sidebar navigation. The expanded/detail view takes the main content area. This is a standard master-detail layout.

### Option C (Timeline River) on Desktop
The horizontal rails become wider, showing more items. The bottom sheet becomes a side panel (slides in from the right). You can have the main canvas + the detail panel open simultaneously. This is the most powerful desktop layout because you maintain overview + detail at the same time.

```
Desktop (1280px+):

+----------------------------------+--------------------+
|  STORY                           |                    |
|  +----------------------------+  |  Kael (v3)        |
|  | "In the ancient city..."   |  |                    |
|  +----------------------------+  |  [portrait]        |
|                                  |                    |
|  CHARACTERS                      |  Description:      |
|  [Kael*] [Lyra] [Maren] [+]    |  Warrior-poet...   |
|                                  |                    |
|  SCENES                          |  [< v2] o o *o*   |
|  [Sc1] [Sc2] [Sc3] [Sc4] [+]  |                    |
|                                  |  Refine:           |
|  PANELS                          |  [____________]    |
|  [img] [img] [img] [img] [+]   |  [Generate ->]     |
|                                  |                    |
+----------------------------------+--------------------+
         Main Canvas (70%)          Detail Panel (30%)
```

---

## Part 7: The Z-Axis (Projections / Layers) -- Future-Proofing

The Z-axis is future work, but the architecture must accommodate it. Here's how each option handles it:

### In Option A (Vertical River)
Projections would be **tabs within a node**. A scene node might have tabs: [Narrative] [Comic] [Audio]. Switching tabs shows the scene in that projection.

### In Option B (Spine and Ribs)
Projections would be an **additional navigation dimension** in the detail view. A sidebar or tab bar within the detail screen.

### In Option C (Timeline River)
Projections are the most natural here. Each flow layer could have a **projection toggle**:

```
  SCENES  [Narrative | Comic | Audio]   <-- projection tabs
  +--------+ +--------+ +--------+
  | Sc. 1  | | Sc. 2  | | Sc. 3  |
  | [comic | | [comic | | [comic |      <-- showing comic projection
  |  panel]| |  panel]| |  panel]|
  +--------+ +--------+ +--------+
```

Switching projections changes what's displayed in the cards without changing the underlying narrative data. This maps perfectly to the simulation-engine's principle that projections are views, not truth.

---

## Part 8: Comparative Analysis

| Criterion | A: Vertical River | B: Spine & Ribs | C: Timeline River |
|-----------|:-:|:-:|:-:|
| Mobile-first simplicity | Strong | Medium | Strong |
| Scalability (many items) | Weak | Strong | Strong |
| Overview at a glance | Weak | Medium | Strong |
| Variation discovery | Medium | Strong | Strong |
| Flow feeling (narrative) | Strong | Weak | Medium |
| Refinement friction | Low | Medium | Low |
| Implementation complexity | Low | Medium | Medium |
| Z-axis readiness | Medium | Medium | Strong |
| Dependency visibility | Strong | Medium | Medium |
| Familiar mobile patterns | Medium | Medium | Strong (Netflix/Spotify) |

---

## Part 9: Recommendation

**Option C (Timeline River) is the strongest foundation**, with selective borrowing from the others.

Here's why, through three lenses:

**Steve Jobs**: "People don't know what they want until you show it to them." The horizontal rail pattern is what every mobile user already knows. Netflix. Spotify. App Store. Instagram Stories. The cognitive load is near zero. Users will understand the layout without explanation. That's the test.

**Don Norman**: "The design of everyday things succeeds when the conceptual model matches the user's mental model." The user thinks: "I have a story, it has characters, they appear in scenes, the scenes become panels." The vertical stacking of labeled rails matches this mental model exactly. Each rail is a category. Scrolling horizontally within a rail is browsing within that category. Opening an item is examining it. This maps directly to how people think about hierarchical creative work.

**Jony Ive**: "Simplicity is not the absence of clutter. It's the result of making sense of complexity." The Timeline River doesn't hide complexity -- it organizes it spatially. The vertical axis provides structure. The horizontal axis provides volume. The bottom sheet / side panel provides depth. Three spatial dimensions, each serving a distinct purpose. Nothing is hidden; everything has a place.

### The Specific Recommendation

1. **Start with Option C as the base layout**: vertical stack of horizontal rails
2. **Borrow the always-visible refinement prompt from the deep-dive** (Part 5): every item has a visible, low-friction path to creating a variation
3. **Borrow the stale cascade visualization**: amber indicators, not blocking, user-initiated refresh
4. **Use bottom sheets on mobile, side panels on desktop** for detail/variation/refinement
5. **Keep the story node as a special full-width card** (not a rail) since there's typically one story with a few variations at most
6. **Implement progressive disclosure**: start with Story + Characters rails only. Add Scenes and Panels rails as the user generates them. The flow grows as the creative work grows.

### What to Build First (v1)

For the immediate implementation:
- The vertical layout with just two rails: **Story** (full-width card) and **Characters** (horizontal rail)
- Tap a character card -> bottom sheet with detail + variation swipe + refine prompt
- Tap [Refine] on story -> inline prompt expands below the story card
- Variation dots on character cards showing version count
- No Z-axis, no stale indicators, no dependency visualization yet

This is a weekend of work that replaces both the stepper and the two-panel split with something that actually scales.

---

## Part 10: Open Questions

1. **Should variations branch or replace?** Currently, refining creates a linear chain (v1 -> v2 -> v3). Should we support branching (v1 -> v2a and v1 -> v2b)? The linear model is simpler. The branching model is more powerful. Recommendation: start linear, add branching when users ask for it.

2. **What happens to the "prompt" as a first-class concept?** In the current story feature, prompts are shown as chat messages. In the Timeline River, prompts are attached to the artifact they produced. Do we keep a chat-like prompt history, or do we attach prompts to artifacts? Recommendation: prompts belong to artifacts, not to a conversation. Each variation knows what prompt created it.

3. **How do we handle the initial empty state?** When a project is new, there are no rails. Just an empty screen. What does the user see? Recommendation: a single input field, centered, with the question "What's your story about?" -- nothing else. The first rail (Story) materializes after the first generation. Then "Extract Characters" appears as a suggestion. The UI builds itself as the user creates.

4. **Where does the "generate next step" action live?** After a story is generated, how does the user trigger character extraction? Recommendation: a **"Continue" action** appears at the bottom of the flow, suggesting the next logical step. It's a suggestion, not a requirement. The user can also add sections manually.

5. **Rail ordering**: Is the vertical order fixed (Story > Characters > Scenes > Panels) or user-configurable? Recommendation: fixed for v1. The dependency graph implies a natural order. Configurability adds complexity without proportional value.
