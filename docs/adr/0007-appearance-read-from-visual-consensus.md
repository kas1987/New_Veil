---
status: accepted
---

# Appearance Read Comes From Visual Consensus

A persona's **Appearance Read** — the look The Veil speaks in a prompt and the look the character atlas shows on a card — comes from visual consensus over that persona's reference frames when a consensus exists. **Identity Canon** (published name, trigger, biography) stays frozen and is never rewritten to match the read. **Synthetic Measure** (generated bust, waist, hips, height, weight) may still fill a card, but it is not the Appearance Read and must not drive the prompt once consensus exists.

## Considered Options

- **Caption and hash as the body:** Author captions and a name hash produced one hair color, one eye color, and a tight bust–waist–hip set for almost every persona. That was stable and required no vision pass. It also invented a body the frames do not show, so prompts and cards disagreed with the reference stills.
- **Write the read into Identity Canon:** Folding vision output into the frozen published metadata would make later rebuilds unable to tell biography from inference, and would let an unreviewed frame majority overwrite the published identity.
- **Second written profile tree as the source of truth:** Copying a full Atlas profile onto disk and editing that copy split the shelf the weights live on from the card the viewer reads. The atlas now assembles the same card shape in memory from the live shelf instead.

## Consequences

- When consensus lands, appearance and body language in the psychometric prompt replace any older clause stored on the persona. The catalog must be reloaded before a running console or Comfy graph sees it.
- Frames that disagree (several bust sizes, several ethnic impressions) stay an unreviewed Appearance Read. They still drive the prompt; they do not become Identity Canon, and they do not get averaged into a fake measurement.
- Synthetic Measure may remain visible beside the read until a measured body exists. Treat those inches as filler. Do not use them to choose bust language once consensus names a size and a hang.
- The only derived text written back onto the shelf persona record is the Appearance Read clauses the prompt already uses. Identity Canon files are not edited.
