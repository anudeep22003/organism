# Progressive Reveal: How the Workspace Builds Itself

**Date**: 2026-02-23  
**Companion to**: `ux-exploration-xyz-patterns.md`, `ux-interaction-patterns.md`

---

## The Core Idea

The workspace is never empty and never overwhelming. It reveals itself in response to the user's creative progress. At any point, the user sees only what exists plus one gentle suggestion of what could come next.

This document walks through the complete lifecycle of a project from first touch to a full comic.

---

## Stage 0: The Blank Slate

```
+----------------------------------+
|  [<- Projects]    New Project    |
+----------------------------------+
|                                  |
|                                  |
|                                  |
|                                  |
|                                  |
|           What's your            |
|          story about?            |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |                            |  |
|  |              [Create ->]   |  |
|  +----------------------------+  |
|                                  |
|                                  |
|                                  |
|                                  |
|                                  |
+----------------------------------+
```

Nothing exists. Nothing is suggested except the one thing that must happen first. The textarea sits in the center of the screen. It is the only interactive element. This is a canvas waiting for the first stroke.

---

## Stage 1: Story Exists

The user typed a prompt and hit Create. The story is streaming. The input lifts up, transforms into the Story section, and text flows in.

```
+----------------------------------+
|  [<- Projects]  My Project  ...  |
+----------------------------------+
|                                  |
|  STORY                           |
|  +------------------------------+|
|  | "Rain hammered the cracked   ||
|  | cobblestones of Vereth as    ||
|  | the last bell tower rang     ||
|  | its hollow note across the   ||
|  | city. Kael stood at the edge ||
|  | of the Bridge of Whispers,   ||
|  | his coat heavy with..."      ||
|  |                         |    ||
|  |  [blinking cursor]          ||
|  +------------------------------+|
|                                  |
|                                  |
|                                  |
+----------------------------------+
```

While streaming, nothing else is shown. Let the user watch their story come to life. Do not distract with buttons or suggestions.

After streaming completes:

```
+----------------------------------+
|  [<- Projects]  My Project  ...  |
+----------------------------------+
|                                  |
|  STORY                        v1 |
|  +------------------------------+|
|  | "Rain hammered the cracked   ||
|  | cobblestones of Vereth as    ||
|  | the last bell tower rang     ||
|  | its hollow note..."          ||
|  |                              ||
|  | [Read more v]               ||
|  +------------------------------+|
|  [Refine]                        |
|                                  |
|  +------------------------------+|
|  | Who lives in this world?     ||
|  |                              ||
|  | [Extract Characters ->]      ||
|  +------------------------------+|
|                                  |
|                                  |
+----------------------------------+
```

The story text truncates with "Read more." A [Refine] button appears below. And the first suggestion card materializes: "Who lives in this world?"

The suggestion card is the **only path forward** shown. Not a menu of 5 options. One.

---

## Stage 2: Characters Exist

The user tapped "Extract Characters." The suggestion card transforms into a CHARACTERS rail as characters stream in one by one.

```
+----------------------------------+
|  [<- Projects]  My Project  ...  |
+----------------------------------+
|                                  |
|  STORY                        v1 |
|  +------------------------------+|
|  | "Rain hammered the cracked   ||
|  | cobblestones of Vereth..."   ||
|  | [Read more v]               ||
|  +------------------------------+|
|  [Refine]                        |
|                                  |
|  CHARACTERS                      |
|  +--------+ +--------+ +------+ |
|  |[shimmer| | Lyra   | | Mar> | |
|  | Kael   | |[shimmer| |      | |
|  | load..]| | load..]| |      | |
|  +--------+ +--------+ +------+ |
|  <--- horizontal scroll --->     |
|                                  |
+----------------------------------+
```

Characters appear as cards in the rail. Initially they have name + description (text only, no images). Shimmer placeholders indicate "there's content here, it's arriving."

After extraction completes:

```
+----------------------------------+
|                                  |
|  STORY                        v1 |
|  +------------------------------+|
|  | "Rain hammered the cracked   ||
|  | cobblestones..."             ||
|  | [Read more v]               ||
|  +------------------------------+|
|  [Refine]                        |
|                                  |
|  CHARACTERS                      |
|  +--------+ +--------+ +------+ |
|  | Kael   | | Lyra   | | Ma>  | |
|  | [text  | | [text  | |      | |
|  |  only] | |  only] | |      | |
|  | v1     | | v1     | |      | |
|  +--------+ +--------+ +------+ |
|                                  |
|  +------------------------------+|
|  | Your characters need faces.  ||
|  |                              ||
|  | [Render All Characters ->]   ||
|  +------------------------------+|
|                                  |
+----------------------------------+
```

Three character cards (text only -- no images yet). And the next suggestion: "Your characters need faces."

The user can also tap any character card to refine its description before rendering. The suggestion doesn't prevent this -- it's a nudge, not a gate.

---

## Stage 3: Characters Have Faces

After rendering, character cards update with portrait images:

```
  CHARACTERS                       
  +--------+ +--------+ +------+ 
  |[portrait| |[portrait| | [p>  | 
  | Kael   | | Lyra   | |      | 
  | v1     | | v1     | |      | 
  +--------+ +--------+ +------+ 
```

Now the user might want to refine some characters. They tap Kael, see the full portrait in the bottom sheet, and submit "make him more weathered, older."

A new variation (v2) generates. The card in the rail updates to show the latest version with variation dots:

```
  +--------+
  |[v2 img]|
  | Kael   |
  | o *o*  |  <-- 2 dots, second active
  +--------+
```

After the user is satisfied with characters, the next suggestion appears:

```
  +------------------------------+
  | Let's break this into        |
  | scenes.                      |
  |                              |
  | [Generate Scenes ->]         |
  +------------------------------+
```

---

## Stage 4: Scenes Exist

```
+----------------------------------+
|  STORY                     v1    |
|  [truncated preview]             |
|  [Refine]                        |
|                                  |
|  CHARACTERS                      |
|  [Kael v2] [Lyra v1] [Maren v1] |
|                                  |
|  SCENES                          |
|  +--------+ +--------+ +------+ |
|  | Sc. 1  | | Sc. 2  | | Sc>  | |
|  | Market | | Betray | |      | |
|  | [K][L] | | [K][M] | |      | |
|  | v1     | | v1     | |      | |
|  +--------+ +--------+ +------+ |
|                                  |
|  +------------------------------+|
|  | Time to bring these scenes  ||
|  | to life.                     ||
|  |                              ||
|  | [Render All Panels ->]       ||
|  +------------------------------+|
|                                  |
+----------------------------------+
```

Scene cards show: scene title, a one-line description, character chips (showing which characters appear), and version indicator.

The user can tap any scene to refine its description, add/remove characters, adjust dialogue, etc.

---

## Stage 5: Full Project

```
+----------------------------------+
|  STORY                     v2    |
|  [truncated preview]             |
|  [Refine]                        |
|                                  |
|  CHARACTERS                      |
|  [Kael v3] [Lyra v2] [Maren v1] |
|                                  |
|  SCENES                          |
|  [Sc1 v1] [Sc2 v2] [Sc3 v1] +  |
|                                  |
|  PANELS                          |
|  +--------+ +--------+ +------+ |
|  | [comic | | [comic | | [c>  | |
|  |  panel]| |  panel]| |      | |
|  | Sc1-p1 | | Sc1-p2 | |      | |
|  | v1     | | v1     | |      | |
|  +--------+ +--------+ +------+ |
|                                  |
|  [Export Comic]                  |
|                                  |
+----------------------------------+
```

The full workspace. Four rails. Every section visible at a glance. The user can scroll to any section, tap into any item, refine any artifact. The [Export Comic] button appears once panels are rendered.

---

## The Key Insight: The Workspace Grows With the Work

At Stage 0, the screen has one element.  
At Stage 1, it has one rail (Story).  
At Stage 2, two rails (Story, Characters).  
At Stage 3, the same two rails, but richer.  
At Stage 4, three rails.  
At Stage 5, four rails plus export.

**The user never sees a screen with empty placeholders for things they haven't created yet.** There is no "Characters (empty)" section before characters are extracted. There is no "Panels (coming soon)" section. Each section materializes when it has content.

This is progressive disclosure at the spatial level. The workspace is as simple as the work demands, at every stage.

---

## What Doesn't Scale (And How We'll Handle It)

### Problem: Many Characters
If the story has 15 characters, the rail becomes long to scroll. 

**Solution**: The rail shows the first ~4 characters with a "+11 more" indicator. Alternatively, the rail can have a filter: [All] [Main] [Supporting]. This keeps the rail manageable while preserving access to everything.

### Problem: Many Scenes  
A full narrative might have 20-30 scenes. Even horizontal scrolling gets tedious.

**Solution**: Scene cards can be grouped by act or chapter. The rail header gets a dropdown:

```
  SCENES  [Act 1 v] [Act 2] [Act 3]
  [Sc1] [Sc2] [Sc3] [Sc4] [+]
```

Tapping an act filter scrolls the rail to that group. This introduces hierarchy without adding navigation complexity.

### Problem: Many Variations
If a character has 12 variations, the dots become unreadable.

**Solution**: At >5 variations, switch from dots to a counter: "v7 of 12" with arrows. In the detail sheet, show a scrollable filmstrip of variation thumbnails instead of dots:

```
  [v1] [v2] [v3] [v4] [v5] [v6] [*v7*] [v8] ...
  <--- horizontal scroll --->
```

### Problem: Deep Dependency Chains
When the story changes, characters are stale. When characters are refreshed, scenes might go stale. When scenes are refreshed, panels go stale. Cascading staleness could make the entire workspace look amber.

**Solution**: Stale state is **lazy and local**. When the story changes:
- Characters are marked stale immediately (they depend directly on story)
- Scenes are NOT marked stale yet (they depend on characters, which haven't changed yet)
- Only when a character is refreshed AND its content actually changes do the scenes using that character become stale
- This prevents speculative staleness cascading

---

## The Emotional Arc of the Experience

Stage 0: **Anticipation.** A blank canvas, a single question. The creative moment before the first word.

Stage 1: **Discovery.** The story streams in. The user watches their idea take form. Surprise and delight as the narrative exceeds their prompt.

Stage 2: **Recognition.** Characters emerge from the story. "Oh, the AI found *that* character in there." The user's story becomes populated.

Stage 3: **Ownership.** The user refines characters, adjusts descriptions, regenerates portraits. The characters become *theirs*, not just the AI's output.

Stage 4: **Architecture.** Scenes impose structure on the narrative. The user sees their story as a sequence of moments, not just text. This is the shift from writer to director.

Stage 5: **Completion.** Visual panels exist. The story is no longer imagined -- it's rendered. The export button is the final handshake: "This is yours now."

At every stage, the workspace grows, but the emotional experience stays grounded in one principle: **you are in control of something that feels alive.**
