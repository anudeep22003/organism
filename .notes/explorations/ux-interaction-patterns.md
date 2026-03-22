# Interaction Patterns: The Timeline River in Detail

**Date**: 2026-02-23  
**Companion to**: `ux-exploration-xyz-patterns.md`  
**Focus**: Mobile-first interaction design for the recommended Option C

---

## 1. The Genesis Moment (Empty State)

The most important screen is the empty one. It sets the tone for everything.

```
+----------------------------------+
|  [<- Projects]    New Project    |
+----------------------------------+
|                                  |
|                                  |
|                                  |
|                                  |
|           What's your            |
|          story about?            |
|                                  |
|  +----------------------------+  |
|  | A warrior-poet in a dying  |  |
|  | kingdom must choose...     |  |
|  |                            |  |
|  |              [Create ->]   |  |
|  +----------------------------+  |
|                                  |
|                                  |
|                                  |
|                                  |
+----------------------------------+
```

One question. One input. Nothing else.

The input is a `textarea` that expands as the user types. It sits in the vertical center of the screen. The placeholder text might rotate through gentle suggestions:

- "A warrior-poet in a dying kingdom..."
- "Two strangers meet on a train going nowhere..."
- "The last librarian guards a book that rewrites itself..."

These are not templates. They're whispers of possibility. They disappear the moment you start typing.

### What Happens on Submit

The input shrinks upward and transforms into the first **Story node**. The text appears character-by-character as the AI streams. The genesis input becomes the first rail.

```
Transition animation (300ms):

1. Input lifts to top of screen
2. "STORY" label fades in above it
3. Story text streams in below the user's prompt
4. When streaming completes, a subtle pulse suggests "what's next"
```

---

## 2. The Suggestion Engine (What Comes Next)

After each generation step, the system suggests the next logical action. This is not a stepper -- it's a gentle nudge that appears at the bottom of the current flow.

```
After story generation:

  STORY
  +------------------------------+
  | "In the war-torn city..."    |
  |              v1    [Refine]  |
  +------------------------------+

  +------------------------------+
  | Ready to meet your           |
  | characters?                  |
  |                              |
  | [Extract Characters ->]      |
  |                              |
  | or continue refining above   |
  +------------------------------+
```

This suggestion card:
- Appears only after the previous step completes
- Is dismissible (swipe away or tap "x")
- Can be ignored -- the user can refine the story instead
- Disappears once the user takes the action

After character extraction:

```
  CHARACTERS
  [Kael] [Lyra] [Maren]

  +------------------------------+
  | Your characters need faces.  |
  |                              |
  | [Render Characters ->]       |
  |                              |
  | or refine their descriptions |
  +------------------------------+
```

The language is conversational, not technical. "Your characters need faces" not "Generate character images." We're building a studio that speaks like a creative partner.

---

## 3. The Card Anatomy (Mobile)

Every item in a rail is a card. Cards have a consistent anatomy across types, with type-specific content areas.

### Character Card (in rail)

```
+------------------+
|  +-----------+   |
|  |           |   |
|  | [portrait |   |
|  |  image]   |   |
|  |           |   |
|  +-----------+   |
|                  |
|  Kael            |
|  Warrior-Poet    |
|                  |
|  o o *o*  v3     |  <-- variation dots + count
+------------------+
   120px x 180px
```

### Scene Card (in rail)

```
+------------------+
|  +-----------+   |
|  | [rendered |   |
|  |  panel]   |   |
|  +-----------+   |
|                  |
|  Scene 1         |
|  Market Square   |
|                  |
|  [Kael] [Lyra]  |  <-- character chips
|  o  v1           |
+------------------+
```

### Story Card (full-width, not in a rail)

```
+----------------------------------+
|  STORY                    v1     |
|  +--------------------------+    |
|  | "In the war-torn city   |    |
|  | of Vereth, where stone  |    |
|  | bridges span chasms     |    |
|  | older than memory, a    |    |
|  | warrior-poet named..."  |    |
|  |                         |    |
|  | [Read more v]           |    |
|  +--------------------------+   |
|              [Refine]           |
+----------------------------------+
```

Story is always full-width because narrative text needs reading width. It truncates at ~6 lines with a "Read more" expander.

---

## 4. The Bottom Sheet (Mobile Detail View)

This is the most important interaction surface. It's where the user examines, compares, and refines.

### Opening the Sheet

Tap any card in a rail. The sheet slides up from the bottom, covering ~85% of the screen. The rail is still visible at the top, slightly dimmed, providing spatial context.

### Sheet Anatomy

```
+----------------------------------+
|  ---- drag handle ----           |
+----------------------------------+
|                                  |
|  Kael                            |
|  Warrior-Poet of Vereth          |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |                            |  |
|  |    [full portrait image]   |  |
|  |                            |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  [< prev]   o o *o*   [next >]  |
|              v3 of 3             |
|                                  |
|  +----- Description ----------+  |
|  | Warrior-poet of the old    |  |
|  | kingdom. Once commanded    |  |
|  | the Southern Verse Guard,  |  |
|  | now wanders the bridges... |  |
|  +----------------------------+  |
|                                  |
|  +----- Traits ---------------+  |
|  | [Stoic] [Poetic] [Scarred] |  |
|  +----------------------------+  |
|                                  |
|  +----- History --------------+  |
|  | v1: extracted from story   |  |
|  | v2: "make him older"       |  |
|  | v3: "add the scar"    <-  |  |
|  +----------------------------+  |
|                                  |
+----------------------------------+
|  +----------------------------+  |
|  | How should this change?    |  |
|  |                            |  |
|  |              [Generate ->] |  |
|  +----------------------------+  |
+----------------------------------+
```

### Key Design Decisions

**The prompt is pinned to the bottom of the sheet**, above the safe area. It's always visible. You never have to scroll to find it or tap a button to reveal it. The question "How should this change?" is the default placeholder -- it frames refinement as a conversation, not a command.

**Variation navigation is prominent** -- swipe left/right on the image, or use the arrows. Dots show position. The version label ("v3 of 3") is explicit.

**History is visible but compact** -- a scrollable list of refinement prompts. Each version links to the prompt that created it. The current version's prompt is marked with an arrow.

**Swiping down dismisses the sheet** -- standard iOS/Android gesture.

### Sheet States

**Generating state** (after submitting a refinement):

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Kael                            |
|  Generating v4...                |
|                                  |
|  +----------------------------+  |
|  |                            |  |
|  |   [shimmer placeholder]    |  |
|  |                            |  |
|  +----------------------------+  |
|                                  |
|  Your ask:                       |
|  "Make his armor more ornate,   |
|   ceremonial rather than        |
|   battle-worn"                   |
|                                  |
+----------------------------------+
|  [Cancel Generation]             |
+----------------------------------+
```

The sheet stays open during generation. The user sees their prompt reflected back to them while they wait. They can cancel and discard.

**Generated state** (result arrives):

The new image/content fades in. The variation dots update (now 4 dots). The prompt input resets, ready for another refinement. The sheet doesn't close -- the user is in a refinement flow and might want to continue.

---

## 5. The Refinement Flow for Story (Special Case)

Story is different from characters/scenes because it's text, not a card. The refinement UX is slightly different.

### Inline Refinement (Mobile)

Tapping [Refine] on the story card slides down an input area below the story:

```
  STORY                        v1
  +------------------------------+
  | "In the war-torn city..."    |
  | [expanded full story text]   |
  +------------------------------+
  
  +------------------------------+
  | What would you change?       |
  |                              |
  | "Make the opening more       |
  |  atmospheric, add weather    |
  |  and sounds of the city"     |
  |                              |
  |              [Generate ->]   |
  +------------------------------+
```

When the new version streams in, it **replaces the story text in-place** while the old version is preserved as v1. The variation indicator updates to v2.

To see the old version: tap the version indicator to open a version comparison bottom sheet:

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  Story Versions                  |
|                                  |
|  [v1]  [*v2*]                   |
|                                  |
|  v2 (current):                   |
|  "Rain hammered the cracked     |
|   cobblestones of Vereth as     |
|   the last bell tower rang..."  |
|                                  |
|  Changed from v1:                |
|  "Added weather, city sounds,   |
|   more atmospheric opening"     |
|                                  |
|  [Use v1]  [Keep v2]            |
|                                  |
+----------------------------------+
```

---

## 6. Stale State and Dependency Cascade

This is the dependency graph made visible. When an upstream artifact changes, downstream artifacts are marked stale.

### What Triggers Staleness

| When this changes... | These become stale... |
|---|---|
| Story text (new version) | All characters (they were extracted from the old story) |
| Character description | Scenes containing that character, rendered images of that character |
| Scene description | Rendered panels of that scene |

### Visual Treatment

Stale cards get a subtle overlay:

```
  CHARACTERS  [3 need refresh]
  +------------------+  +------------------+
  |  +-----------+   |  |  +-----------+   |
  |  | [portrait |   |  |  | [portrait |   |
  |  |  faded/   |   |  |  |  faded/   |   |
  |  |  amber    |   |  |  |  amber    |   |
  |  |  tint]    |   |  |  |  tint]    |   |
  |  +-----------+   |  |  +-----------+   |
  |  Kael        [!] |  |  Lyra        [!] |
  |  Warrior-Poet    |  |  Oracle          |
  +------------------+  +------------------+
```

- The image gets a slight desaturation + amber tint
- A small [!] badge appears
- The section header shows a count: "3 need refresh"

### Refresh Actions

**Per-item**: Tap a stale card -> bottom sheet shows "This is based on an older version of the story. [Refresh] or [Keep as-is]"

**Per-section**: The section header has a [Refresh All] action that regenerates all stale items in that rail.

**Cascade refresh**: After refreshing characters, if scenes were also stale, they remain stale (they don't auto-refresh). The user controls propagation speed. This is intentional -- cascading auto-refresh would be jarring and expensive.

---

## 7. Adding Items Manually

Sometimes the user wants to add something that wasn't auto-generated. A character that wasn't in the story. An extra scene.

### The Add Button

Each rail (except Story) has a [+] button as the last card in the rail:

```
  CHARACTERS                           
  [Kael] [Lyra] [Maren] [+]  <-- scroll to end
```

The [+] card is a dashed-border ghost card:

```
+------------------+
|                  |
|                  |
|       [+]        |
|                  |
|   Add Character  |
|                  |
+------------------+
```

Tapping it opens a bottom sheet with two options:

```
+----------------------------------+
|  ---- drag handle ----           |
|                                  |
|  New Character                   |
|                                  |
|  [Describe from scratch]         |
|  Write a description and let     |
|  AI generate the character       |
|                                  |
|  [Extract from story]            |
|  Point to a part of the story    |
|  and pull out a character         |
|                                  |
+----------------------------------+
```

---

## 8. Desktop Adaptations

### The Side Panel (Replaces Bottom Sheet)

On desktop (>768px), tapping a card opens a side panel instead of a bottom sheet:

```
+--------------------------------------+--------------------+
|                                      |                    |
|  STORY                         v2    |  Kael              |
|  +------------------------------+    |  Warrior-Poet      |
|  | "Rain hammered the cracked   |    |                    |
|  | cobblestones of Vereth..."   |    |  [portrait img]    |
|  +------------------------------+    |                    |
|                                      |  o o *o*  v3       |
|  CHARACTERS                          |                    |
|  [*Kael*] [Lyra] [Maren] [Thn] [+] |  Description:      |
|                                      |  "Warrior-poet of  |
|  SCENES                              |  the old kingdom"  |
|  [Sc1] [Sc2] [Sc3] [Sc4] [+]      |                    |
|                                      |  Traits:           |
|  PANELS                              |  [Stoic] [Poetic]  |
|  [img] [img] [img] [img] [+]       |                    |
|                                      |  [______________]  |
|                                      |  [Generate ->]     |
+--------------------------------------+--------------------+
```

The selected card in the rail gets a visual highlight (border, subtle background). The side panel shows the full detail. **The canvas remains visible** -- you can see your entire project while examining a single item.

### Inline Prompt on Hover (Desktop Enhancement)

On desktop, hovering over a card reveals a small prompt trigger at the bottom of the card:

```
Hover state:
+------------------+
|  [portrait]      |
|                  |
|  Kael            |
|  Warrior-Poet    |
|  o o *o*  v3     |
|  [Refine...]     |  <-- appears on hover
+------------------+

Click [Refine...]:
+------------------+
|  [portrait]      |
|  Kael            |
|  [____________]  |  <-- inline prompt
|  [Generate ->]   |
+------------------+
```

The card expands slightly to accommodate the inline prompt. The refinement happens without opening the side panel. Quick, surgical edits. For deeper examination, click the card to open the side panel.

---

## 9. Gesture Summary

| Gesture | Mobile | Desktop |
|---|---|---|
| Scroll vertically | Browse flow (story -> characters -> scenes) | Same |
| Scroll horizontally (in rail) | Browse items in a category | Same |
| Tap card | Open bottom sheet (detail + refine) | Open side panel |
| Swipe left/right on image (in sheet) | Navigate variations | Navigate variations |
| Tap [Refine] on story card | Expand inline prompt below story | Same |
| Hover on card | N/A | Reveal quick-refine affordance |
| Swipe down on sheet | Dismiss | N/A (click outside) |
| Long press on card | Future: reorder, delete, compare | Right-click context menu |

---

## 10. Animation and Transition Principles

All transitions should feel physical -- things have weight, momentum, and position.

1. **Bottom sheet**: Slides up with spring physics (slight overshoot, settle). Drag down to dismiss with velocity-sensitive release.

2. **Card generation**: New cards materialize with a fade + slight scale-up (0.95 -> 1.0, 200ms ease-out). Never pop in.

3. **Variation swipe**: Content slides horizontally with momentum. Dots update mid-transition.

4. **Streaming text**: Characters appear individually, left to right, at ~30 chars/sec. No chunk jumps.

5. **Stale indicator**: Fades in over 500ms after the upstream change completes. Not instant -- the cause should be visible before the effects.

6. **Rail appearance**: When a new section appears (e.g., Characters rail after extraction), it slides up from below the fold with a 300ms ease-out. The user's scroll position adjusts to keep the current view stable.

7. **Suggestion cards**: Fade in with a 1-second delay after the generation completes. Give the user a moment to appreciate what was just created before suggesting next steps.

---

## 11. Accessibility Notes

- All interactive elements must be reachable via keyboard (Tab, Enter, Escape)
- Bottom sheets must trap focus and be dismissible via Escape
- Variation navigation must work with arrow keys, not just swipe
- Stale indicators must have ARIA labels ("Character Kael is out of date")
- Rail horizontal scrolling must be navigable with arrow keys
- The prompt input must have a visible label (even if visually the placeholder serves that role)
- Color is never the only indicator of state -- stale items have both color change AND icon
