# Scene Engine — Agent Notes

## Modal stacking context

All overlay layers (backdrop z-10, modal z-20, sub-modal z-30) must be rendered as
direct children of the **step root**, not inside a scrolling list container. If a modal
is anchored to a container with `overflow-y-auto`, scrolling the list moves the modal.

The step root is `relative`, stable, and non-scrolling — that is the correct anchor.

**Known tension:** this breaks the natural ownership chain where a modal (z-20) would
open its own sub-modal (z-30). The alternative is `fixed` positioning on z-30 layers,
which lets the modal own the transition but covers the full viewport including chrome.
Not yet implemented — revisit when the UX for focused inspection states is more defined.
