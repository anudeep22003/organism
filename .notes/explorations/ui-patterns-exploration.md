# UI Patterns Exploration: The Narrative Engine

A design exploration by the studio of Norman, Ive & Jobs.

---

## Part 1: First Principles

Before drawing anything, we must name what we are actually designing.

We are designing **a creative instrument**.

Not a form. Not a wizard. Not a chat. Not a dashboard.

An instrument is something you learn once, then play forever. A piano has 88 keys. You see them all. You play what you need. The complexity is in you, not in the interface.

Three forces shape this instrument:

1. **Flow** (Y-axis) — The vertical spine. Story flows downward. World begets Characters begets Scenes begets Output. This is gravity. This is causality.

2. **Variation** (X-axis) — Alternatives. You generated a character, but you want another take. You rewrote a scene description. This is branching. This is taste.

3. **Projection** (Z-axis, future) — The same scene rendered as comic, audio, film. This is media. This comes later.

The question is: **How do we make Flow and Variation feel inevitable on a 375px screen?**

---

## Part 2: What We Know

From studying the codebase:

**The stepper (comic-builder) fails because:**
- It forces linear progression. Creativity is not linear.
- It hides context. You can't see the story while editing characters.
- It doesn't support going back and changing something upstream.
- It has no concept of "this changed, so that is stale."

**The side-by-side (story feature) fails because:**
- It only handles one entity (story text). No characters, no scenes.
- The split layout wastes mobile space.
- The prompt-on-left, output-on-right model doesn't extend to multiple entities.
- It's a chat interface pretending to be a workspace.

**What must survive into the new design:**
- Streaming text generation (works well)
- React Query + event-driven cache updates (clean pattern)
- The InputBox component (reusable)
- shadcn/Radix UI primitives
- Mobile toggle pattern (the concept, not the implementation)

---

## Part 3: The Vertical Spine (Y-Axis)

The Y-axis is the backbone. Everything else hangs off it.

### Principle: One scroll, infinite depth.

The user scrolls down through their world. Each section is a **card** or **block** that represents one layer of the narrative. The document never ends — it grows as the story grows.

### What the spine looks like:

```
┌─────────────────────────────┐
│  PROJECT: "The Last Ember"  │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  STORY                      │
│  "In a world where..."      │
│  ░░░░░░░░░░░░░░░░░░░░░░░░  │  ← collapsed preview
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  CHARACTERS                 │
│  ┌──────┐ ┌──────┐         │
│  │Ember │ │Voidk │         │  ← horizontal scroll of cards
│  │  🔥  │ │  ⚫  │  (+)    │
│  └──────┘ └──────┘         │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  SCENES                     │
│  Scene 1: The Awakening     │
│  Scene 2: The Confrontation │  ← vertical list
│  Scene 3: The Escape        │
│  (+)                        │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  OUTPUT                     │
│  [Generate Comic]           │
│  ░░░░░░░░░░░░░░░░░░░░░░░░  │
└─────────────────────────────┘
```

This is the resting state. Collapsed. Calm. You see everything at once.

---

## Part 4: The Variation Problem (X-Axis)

This is the hard problem. How do you show "Version A" vs "Version B" of a character description? Of a rendered image? Of a scene?

### Constraint: Mobile is 375px wide. You cannot show two versions side-by-side.

This eliminates the obvious answer (horizontal scroll of full cards). On mobile, you need a different metaphor.

Let me present five options.

---

### Option A: "The Stack" — Swipeable Cards

**Metaphor:** A deck of cards. The current version is on top. Swipe left to see alternatives. Swipe right to go back.

```
MOBILE:
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │                       │  │
│  │  "A fire spirit who   │  │
│  │   lost her flame..."  │  │
│  │                       │  │
│  │  ● ○ ○    ← dots     │  │
│  └───────────────────────┘  │
│     ← swipe →               │
│                              │
│  [Prompt: "Make her older"]  │  ← inline prompt
└─────────────────────────────┘

After swiping left:

┌─────────────────────────────┐
│  EMBER (v2)                 │
│  ┌───────────────────────┐  │
│  │  [New Character Image]│  │
│  │                       │  │
│  │  "An ancient fire     │  │
│  │   keeper, weathered   │  │
│  │   by centuries..."    │  │
│  │                       │  │
│  │  ○ ● ○    ← dots     │  │
│  └───────────────────────┘  │
│     ← swipe →               │
│                              │
│  [Prompt: "Try again"]       │
└─────────────────────────────┘

DESKTOP (wider):
┌─────────────────────────────────────────────────┐
│  EMBER                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────┐ │
│  │ v1           │  │ v2 (active)  │  │  (+)  │ │
│  │ [image]      │  │ [image]      │  │       │ │
│  │ "A fire..."  │  │ "An ancient" │  │       │ │
│  └──────────────┘  └──────────────┘  └───────┘ │
│                                                  │
│  [Prompt: "Make her more menacing"]              │
└─────────────────────────────────────────────────┘
```

**Strengths:**
- Familiar mobile pattern (Stories, Tinder, photo galleries)
- Zero learning curve
- Clean. One thing at a time.
- Dot indicators show count without clutter
- Desktop naturally upgrades to side-by-side

**Weaknesses:**
- Hidden versions. You can't compare at a glance on mobile.
- Swiping is invisible until you know it's there (discoverability)
- Need to manage "active" vs "alternative" states

**Don Norman says:** "The swipe is a hidden affordance. You must signal it — dots, a peek of the next card, a subtle shadow edge."

**Jony Ive says:** "This is the right level of restraint. One version, full attention. The alternatives exist but don't compete."

**Steve Jobs says:** "Ship this first. It works."

---

### Option B: "The Filmstrip" — Horizontal Scroll Rail

**Metaphor:** A filmstrip. Versions are frames on a horizontal rail. The rail sits below the current active version.

```
MOBILE:
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Active Version]     │  │
│  │  "A fire spirit who   │  │
│  │   lost her flame..."  │  │
│  └───────────────────────┘  │
│                              │
│  ┌────┐ ┌────┐ ┌────┐      │
│  │ v1 │ │ v2 │ │(+) │ →    │  ← thumbnail rail
│  │ ██ │ │ ██ │ │    │      │
│  └────┘ └────┘ └────┘      │
│                              │
│  [Prompt: "Change her era"] │
└─────────────────────────────┘

Tapping v2 thumbnail:

┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Version 2 - Active] │  │
│  │  "An ancient fire     │  │
│  │   keeper..."          │  │
│  └───────────────────────┘  │
│                              │
│  ┌────┐ ┌────┐ ┌────┐      │
│  │ v1 │ │*v2*│ │(+) │ →    │  ← v2 highlighted
│  │ ██ │ │ ██ │ │    │      │
│  └────┘ └────┘ └────┘      │
│                              │
│  [Prompt]                    │
└─────────────────────────────┘
```

**Strengths:**
- All versions visible simultaneously (thumbnails)
- Tap to switch — direct manipulation
- (+) button is always visible — clear affordance for "generate new version"
- The rail metaphor scales: 2 versions or 20

**Weaknesses:**
- Thumbnails are tiny on mobile (maybe 60px). Hard to distinguish.
- Two visual zones (main + rail) add cognitive load
- When you have only one version, the rail feels wasteful

**Don Norman says:** "The filmstrip makes the system model visible. You can see how many versions exist. Good conceptual model."

**Jony Ive says:** "The thumbnails must be beautiful enough to be useful at 60px. If they're just grey blobs, this fails."

**Steve Jobs says:** "Hide the rail when there's only one version. Show it the moment a second version exists. Don't show the scaffolding before you need it."

---

### Option C: "The Timeline" — Version History as Vertical Stack

**Metaphor:** Git log. Versions stack vertically within the entity, newest on top. The active version is expanded, others are collapsed to one line.

```
MOBILE:
┌─────────────────────────────┐
│  EMBER                      │
│                              │
│  ┌───────────────────────┐  │
│  │ ★ Current (v3)        │  │  ← expanded, active
│  │ [Character Image]     │  │
│  │ "An ancient fire      │  │
│  │  keeper, battle-worn" │  │
│  └───────────────────────┘  │
│                              │
│  ├─ v2: "An ancient fire │  │  ← collapsed
│  │      keeper..."        │  │
│  ├─ v1: "A fire spirit   │  │  ← collapsed
│  │      who lost..."     │  │
│                              │
│  [Prompt: "Add scars"]       │
└─────────────────────────────┘

Tapping v1:

┌─────────────────────────────┐
│  EMBER                      │
│                              │
│  ├─ v3: "An ancient fire │  │  ← collapsed
│  │      keeper, battle..." │  │
│  ├─ v2: "An ancient fire │  │  ← collapsed
│  │      keeper..."        │  │
│                              │
│  ┌───────────────────────┐  │
│  │ v1 (viewing)          │  │  ← expanded
│  │ [Original Image]      │  │
│  │ "A fire spirit who    │  │
│  │  lost her flame..."   │  │
│  │                       │  │
│  │  [Use This] [Discard] │  │
│  └───────────────────────┘  │
│                              │
│  [Prompt: "Start fresh"]    │
└─────────────────────────────┘
```

**Strengths:**
- Full history visible
- Familiar mental model (document history, undo stack)
- No horizontal scrolling needed
- Works identically on mobile and desktop

**Weaknesses:**
- Eats vertical space. The Y-axis is already for flow — using it for variations too creates confusion about what "scrolling down" means. Are you going deeper in the flow or seeing older versions?
- Breaks the X/Y mental model. Variations are supposed to be horizontal.
- Gets long fast with many versions.

**Don Norman says:** "This conflates two meanings of vertical: structure and history. That's a mapping violation."

**Jony Ive says:** "It's honest. But it's not elegant."

**Steve Jobs says:** "No. The vertical axis means one thing. Don't pollute it."

---

### Option D: "The Drawer" — Slide-Up Panel for Variations

**Metaphor:** iOS share sheet / bottom drawer. The current version is shown in the spine. When you want to see alternatives, you pull up a drawer that reveals all versions.

```
MOBILE (resting state):
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │  "A fire spirit..."   │  │
│  │                       │  │
│  │  v3 of 3  ▼           │  │  ← version indicator, tappable
│  └───────────────────────┘  │
│                              │
│  [Prompt]                    │
└─────────────────────────────┘

After tapping "v3 of 3 ▼":

┌─────────────────────────────┐
│  EMBER           (dimmed)   │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │                       │  │
│  │                       │  │
├─────────────────────────────┤
│  ┌───────────────────────┐  │  ← drawer slides up
│  │  VERSIONS             │  │
│  │                       │  │
│  │  ┌────┐ ┌────┐ ┌────┐│  │
│  │  │ v1 │ │ v2 │ │*v3*││  │
│  │  │ 🖼  │ │ 🖼  │ │ 🖼  ││  │
│  │  │text │ │text│ │text││  │
│  │  └────┘ └────┘ └────┘│  │
│  │                       │  │
│  │  [+ Generate New]     │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

**Strengths:**
- Spine stays clean. Variations don't clutter the flow.
- Familiar mobile pattern (bottom sheet)
- Can show rich version cards in the drawer
- Explicit action to enter "variation mode" — no accidental swipes

**Weaknesses:**
- Extra tap to access versions. Friction.
- The drawer occludes the spine — you lose context.
- Doesn't feel "spatial." It feels like a menu.
- On desktop, bottom drawers feel odd.

**Don Norman says:** "The drawer hides the conceptual model. The user can't see that alternatives exist until they look for them."

**Jony Ive says:** "A drawer is a storage metaphor. We're not storing things. We're exploring possibilities."

**Steve Jobs says:** "Too many taps. Make it one tap less."

---

### Option E: "The Track" — Inline Horizontal Peek

**Metaphor:** A train track. The current version occupies the full width. But the edges of alternative versions peek from left and right, inviting a horizontal scroll.

```
MOBILE:
┌─────────────────────────────┐
│  EMBER                      │
│                              │
│ ▐┌───────────────────────┐▌ │
│ ▐│  [Character Image]    │▌ │  ← edges of v1 and v3
│ ▐│                       │▌ │     peek from sides
│ ▐│  "A fire spirit who   │▌ │
│ ▐│   lost her flame..."  │▌ │
│ ▐│                       │▌ │
│ ▐│  v2 · ● ○             │▌ │
│ ▐└───────────────────────┘▌ │
│                              │
│  [Prompt: "More menacing"]   │
└─────────────────────────────┘

After scrolling right:

┌─────────────────────────────┐
│  EMBER                      │
│                              │
│  ┌───────────────────────┐▌ │
│  │  [New Character Image]│▌ │
│  │                       │▌ │
│  │  "A fire spirit,      │▌ │
│  │   menacing and wild"  │▌ │
│  │                       │▌ │
│  │  v3 · ○ ●      (+)   │▌ │
│  └───────────────────────┘▌ │
│                              │
│  [Prompt]                    │
└─────────────────────────────┘

DESKTOP:
┌──────────────────────────────────────────────────────┐
│  EMBER                                               │
│                                                       │
│  ┌────────────────┐  ┌────────────────┐  ┌────────┐ │
│  │  v1             │  │  v2 ★ active   │  │  (+)   │ │
│  │  [image]        │  │  [image]       │  │        │ │
│  │  "A fire..."    │  │  "An ancient." │  │ + New  │ │
│  └────────────────┘  └────────────────┘  └────────┘ │
│                                                       │
│  [Prompt: "Try a younger version"]                    │
└──────────────────────────────────────────────────────┘
```

**Strengths:**
- The peek reveals hidden content. Discoverability through physics.
- One gesture (swipe) to navigate. No taps, no menus.
- Dots + peek = double signaling of alternatives
- Desktop expands naturally to show all versions
- (+) is reachable by scrolling to the end — the track has a terminus
- Preserves X-axis mental model: variations are literally horizontal

**Weaknesses:**
- The peek requires careful CSS (overflow, snap points, padding)
- If the card content varies in height, the track may feel jumpy
- Must handle "only one version" gracefully (no peek, no dots)

**Don Norman says:** "The peek is a brilliant affordance. It says 'there's more here' without saying it with words. The physical metaphor maps correctly — horizontal means alternatives."

**Jony Ive says:** "This is the one. The edge peek is like holding a stack of photos — you can see there are more without fanning them out. It respects attention."

**Steve Jobs says:** "Show me one thing. Hint at the rest. Let me pull when I'm ready. This is it."

---

## Part 5: Recommendation Matrix

| Criteria                      | A: Stack | B: Film | C: Timeline | D: Drawer | E: Track |
|-------------------------------|----------|---------|-------------|-----------|----------|
| Mobile-first                  | ★★★★★   | ★★★☆☆  | ★★★★☆      | ★★★★☆    | ★★★★★   |
| Discoverability               | ★★☆☆☆   | ★★★★☆  | ★★★★★      | ★★☆☆☆    | ★★★★☆   |
| Preserves X/Y mental model    | ★★★★☆   | ★★★★☆  | ★☆☆☆☆      | ★★★☆☆    | ★★★★★   |
| Scales to many versions       | ★★★★☆   | ★★★★★  | ★★☆☆☆      | ★★★★☆    | ★★★★★   |
| Desktop upgrade               | ★★★★☆   | ★★★★★  | ★★★☆☆      | ★★☆☆☆    | ★★★★★   |
| Implementation simplicity     | ★★★★★   | ★★★☆☆  | ★★★★☆      | ★★★★☆    | ★★★☆☆   |
| Cognitive load (low = good)   | ★★★★★   | ★★★☆☆  | ★★☆☆☆      | ★★★★☆    | ★★★★☆   |
| Delight                       | ★★★☆☆   | ★★★☆☆  | ★★☆☆☆      | ★★☆☆☆    | ★★★★★   |

**Our recommendation: Option E (The Track), with Option A (The Stack) as fallback for v1 simplicity.**

E is the correct metaphor. A is the fastest to ship. You could ship A first and evolve to E.

---

## Part 6: The Prompt Interaction Pattern

Regardless of which variation pattern you choose, you need to answer: **How does the user modify something?**

### The Problem

Every entity in the spine (story, character, scene) is AI-generated. To modify it, the user doesn't edit directly — they prompt the AI. So every entity needs an attached prompt surface.

### Three patterns for prompting:

#### Pattern 1: "Inline Prompt" — Always Visible

```
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │  "A fire spirit..."   │  │
│  └───────────────────────┘  │
│                              │
│  ┌───────────────────────┐  │
│  │ Change Ember...       │  │  ← always-visible input
│  └───────────────────────┘  │
└─────────────────────────────┘
```

**Pros:** Zero friction. Always ready.
**Cons:** Visual noise. Every section has an input box. The spine becomes a form.

#### Pattern 2: "Tap to Prompt" — Contextual Reveal

```
Resting:
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │  "A fire spirit..."   │  │
│  │                  [✎]  │  │  ← subtle edit affordance
│  └───────────────────────┘  │
└─────────────────────────────┘

After tapping ✎:
┌─────────────────────────────┐
│  EMBER                      │
│  ┌───────────────────────┐  │
│  │  [Character Image]    │  │
│  │  "A fire spirit..."   │  │
│  └───────────────────────┘  │
│                              │
│  ┌───────────────────────┐  │
│  │ What would you change? │  │  ← revealed input
│  │ ________________________│  │
│  │ [Generate New Version]  │  │
│  └───────────────────────┘  │
└─────────────────────────────┘
```

**Pros:** Clean resting state. Prompt only when wanted.
**Cons:** Extra tap. The ✎ is small.

#### Pattern 3: "Unified Command Bar" — One Prompt to Rule Them All

```
┌─────────────────────────────┐
│  PROJECT: The Last Ember    │
│                              │
│  [Story section]             │
│  [Characters section]        │
│  [Scenes section]            │
│                              │
│ ┌───────────────────────────┐│
│ │ What would you like to    ││  ← fixed bottom bar
│ │ change? @ to target...    ││
│ └───────────────────────────┘│
└─────────────────────────────┘

User types: "@Ember make her older and battle-scarred"
System: Updates Ember, marks downstream as stale.

User types: "Add a new character, a shadow thief"
System: Creates character, appends to Characters section.

User types: "Rewrite scene 2 with more tension"
System: Creates new version of Scene 2.
```

**Pros:** One input for everything. Powerful. Scales infinitely. Familiar (Slack, Linear, Spotlight).
**Cons:** Requires NLU to route commands. "@" mention system needs entity awareness. More engineering.

### Recommendation

**Ship Pattern 2 first. Build toward Pattern 3.**

Pattern 2 (Tap to Prompt) keeps the spine clean and gives you per-entity control without building a command parser. Pattern 3 (Unified Command Bar) is the endgame — it's what makes this feel like a studio instrument — but it requires entity mention resolution and NLU routing.

You could also **combine Pattern 2 + Pattern 3**: each entity has an edit affordance AND there's a global command bar. The command bar is the power user path. The edit icon is the beginner path. Same system, two entry points.

---

## Part 7: The Full Composition — Mobile

Combining the vertical spine + Option E (Track) + Pattern 2 (Tap to Prompt):

```
┌──────────────────────────────┐
│  ☰  The Last Ember      ⚙   │  ← sticky header
├──────────────────────────────┤
│                               │
│  STORY                        │
│  ┌────────────────────────┐   │
│  │ "In a world where      │   │
│  │  fire spirits once     │   │
│  │  ruled the sky..."     │   │  ← collapsed to 3 lines
│  │              [✎] [▾]   │   │     ✎ = prompt, ▾ = expand
│  └────────────────────────┘   │
│          │                    │
│          ▼                    │
│  CHARACTERS                   │
│  ┌────────────────────────┐   │
│ ▐│  ┌──────┐              │▌  │  ← track with peek
│ ▐│  │ 🔥   │  Ember       │▌  │
│ ▐│  │      │  Fire spirit  │▌  │
│ ▐│  └──────┘          [✎] │▌  │
│ ▐│  ● ○                   │▌  │  ← 2 versions
│  └────────────────────────┘   │
│                               │
│  ┌────────────────────────┐   │
│  │  ┌──────┐              │   │
│  │  │ ⚫   │  Voidkeeper  │   │  ← single version, no peek
│  │  │      │  Shadow lord  │   │
│  │  └──────┘          [✎] │   │
│  └────────────────────────┘   │
│                               │
│  [+ Add Character]            │
│          │                    │
│          ▼                    │
│  SCENES                       │
│  ┌────────────────────────┐   │
│  │ 1. The Awakening       │   │
│  │    "Ember wakes in..." │   │
│  │    ⚠ stale         [✎] │   │  ← staleness indicator
│  └────────────────────────┘   │
│  ┌────────────────────────┐   │
│  │ 2. The Confrontation   │   │
│  │    "Voidkeeper desc..."│   │
│  │                    [✎] │   │
│  └────────────────────────┘   │
│                               │
│  [+ Add Scene]                │
│          │                    │
│          ▼                    │
│  OUTPUT                       │
│  ┌────────────────────────┐   │
│  │  [Generate Comic]      │   │
│  │  6 panels ready        │   │
│  └────────────────────────┘   │
│                               │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │  ← fixed bottom
│ │ Tell me what to change...│ │     global command bar
│ └──────────────────────────┘ │     (future: Pattern 3)
└──────────────────────────────┘
```

### After tapping ✎ on Ember:

```
┌──────────────────────────────┐
│  ← Back       Ember      ⚙   │  ← context shifts to entity
├──────────────────────────────┤
│                               │
│  ┌────────────────────────┐   │
│  │  [Character Image]     │   │
│  │                        │   │
│  │  Name: Ember           │   │
│  │  Type: Fire Spirit     │   │
│  │  Role: Protagonist     │   │
│  │                        │   │
│  │  "A fire spirit who    │   │
│  │   lost her flame in    │   │
│  │   the great dimming."  │   │
│  └────────────────────────┘   │
│                               │
│  HISTORY                      │
│  ├─ "Make her older" → v2     │
│  └─ Original extraction → v1  │
│                               │
├──────────────────────────────┤
│ ┌──────────────────────────┐ │
│ │ How should Ember change? │ │  ← contextual prompt
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

This is a **detail view** — you navigated into the entity. The spine is the overview. The detail is the workshop.

---

## Part 8: The Full Composition — Desktop

On desktop (>768px), the spine gets more room. Variations unfold naturally.

```
┌──────────────────────────────────────────────────────────────┐
│  ☰  The Last Ember                                       ⚙  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  STORY                                                       │
│  ┌──────────────────────────────────────────────────────┐    │
│  │ "In a world where fire spirits once ruled the sky,   │    │
│  │  one ember refused to die..."                        │    │
│  │                                                 [✎]  │    │
│  └──────────────────────────────────────────────────────┘    │
│          │                                                   │
│          ▼                                                   │
│  CHARACTERS                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Ember         │  │ Ember (v2)    │  │     (+)       │   │
│  │ ┌───────────┐ │  │ ┌───────────┐ │  │               │   │
│  │ │  🔥 image │ │  │ │  🔥 image │ │  │  + Generate   │   │
│  │ └───────────┘ │  │ └───────────┘ │  │    New        │   │
│  │ "A fire..."   │  │ "An ancient." │  │               │   │
│  │          [✎]  │  │     ★ active  │  │               │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                              │
│  ┌───────────────┐                                          │
│  │ Voidkeeper    │                                          │
│  │ ┌───────────┐ │                                          │
│  │ │  ⚫ image │ │                                          │
│  │ └───────────┘ │                                          │
│  │ "A shadow..." │                                          │
│  │          [✎]  │                                          │
│  └───────────────┘                                          │
│                                                              │
│  [+ Add Character]                                          │
│          │                                                   │
│          ▼                                                   │
│  SCENES                                                      │
│  ...                                                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Tell me what to change...                             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

On desktop, character versions lay out horizontally without any swiping. The track becomes a row. Same data, different projection.

---

## Part 9: Staleness & Dependency (The Ripple)

When a user changes a character, downstream entities may be affected.

### Visual pattern:

```
Before change:

│  Ember ★ active (v2)        │  ← clean
│  Scene 1                    │  ← clean
│  Scene 3                    │  ← clean

After user prompts "Make Ember older":

│  Ember ★ active (v3)        │  ← new, fresh
│  Scene 1  ⚠ May be affected │  ← amber indicator
│  Scene 3  ⚠ May be affected │  ← amber indicator

│  ┌────────────────────────┐  │
│  │ Ember changed.          │  │  ← subtle system message
│  │ 2 scenes may need       │  │     in the spine
│  │ updating.               │  │
│  │ [Update All] [Dismiss]  │  │
│  └────────────────────────┘  │
```

### Rules:
1. Never auto-regenerate. The user chooses.
2. Mark stale entities with a subtle amber indicator.
3. Offer a bulk "Update All" downstream action.
4. Show what changed and what depends on it.

This is the dependency graph made visible. Don Norman's "Gulf of Evaluation" — the user can see the system's state.

---

## Part 10: Implementation Phasing

### Phase 1: The Spine (ship first)
- Vertical scroll with sections: Story, Characters, Scenes, Output
- Each section is collapsible
- Data fetched via React Query
- No variations yet — just the current version of everything

### Phase 2: Inline Prompting
- Add ✎ affordance to each entity card
- Tapping opens detail view (mobile) or inline prompt (desktop)
- Prompt generates a new version, replacing current

### Phase 3: Variations (The Track)
- When a new version is created, keep the old one
- Show dot indicators / horizontal peek
- Implement CSS scroll-snap for mobile swipe
- Desktop: side-by-side cards

### Phase 4: Staleness
- Track dependencies between entities
- Mark downstream entities as stale when upstream changes
- Show system messages for cascading **changes**

### Phase 5: Global Command Bar
- Fixed bottom input
- @ mention system for targeting entities
- NLU routing for commands

---

## Part 11: What This Is NOT

To stay focused, let's name what we are deliberately not building in the UI:

- **Not a chat interface.** The spine is a document, not a conversation.
- **Not a node graph.** Dependency exists but is invisible unless triggered.
- **Not a timeline editor.** Scenes are ordered but not time-coded.
- **Not a dashboard.** There are no metrics, no charts, no status panels.
- **Not a canvas.** You don't drag things around. The spine has gravity.

We are building **a vertical creative workspace with horizontal branching and contextual AI prompting.**

That's one sentence. That should be the pitch.

---

## Appendix: Component Mapping

How this maps to the existing codebase:

| Concept | Current Component | New Component |
|---------|-------------------|---------------|
| Spine | ComicBuilder (stepper) | `<NarrativeSpine />` |
| Story section | WriteStoryPhase | `<StoryBlock />` |
| Character section | ExtractCharactersPhase + GenerateCharacterPhase | `<CharacterBlock />` |
| Character card | CharacterCard | `<EntityCard variant="character" />` |
| Scene section | GeneratePanelsPhase | `<SceneBlock />` |
| Output section | RenderPanelsPhase + ExportPanelsPhase | `<OutputBlock />` |
| Version track | (nothing) | `<VersionTrack />` |
| Prompt input | InputArea / InputBox | `<EntityPrompt />` |
| Stale indicator | (nothing) | `<StaleIndicator />` |
| Detail view | (nothing) | `<EntityDetail />` |
| Command bar | (nothing) | `<CommandBar />` |

---

*"Design is not just what it looks like and feels like. Design is how it works." — Steve Jobs*

*"The real problem with the interface is that it is an interface." — Don Norman*

*"True simplicity is derived from so much more than just the absence of clutter and ornamentation. It's about bringing order to complexity." — Jony Ive*
