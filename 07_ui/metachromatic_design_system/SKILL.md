---
name: metachromatic-design
description: Use this skill to generate well-branded interfaces and assets for MetaChromatic, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.

If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.

## Key files
- `README.md` — full brand definition: content voice, visual foundations, iconography.
- `colors_and_type.css` — all CSS custom properties + `.mc-h1`/`.mc-body`/etc semantic classes. Always link this file first.
- `assets/` — brand mark SVG + PNG exports (16 → 1024 px).
- `preview/` — individual specimen cards showing every token in context.
- `ui_kits/mobile/` — React components (vanilla JSX via Babel) recreating the shipping mobile app. Copy components from here when building new surfaces.

## Quick rules
- Dark-mode-first. Never pure black — always navy-tinted (`#050812` app base, `#0a0e1a` surface).
- White text at 95/65/40/20% opacity. No gray ramp.
- Cyan `#06b6d4` is the default accent; the brand's full prismatic spectrum is for hero gradients, not UI chrome.
- Glass everywhere: `backdrop-filter: blur(8|16|24|40)` + `rgba(255,255,255,0.08)` hairline borders + deep black shadows.
- Medium radii — 12 px inputs, 16 px cards, 24 px modals.
- Primary button = cool cyan→teal gradient (NOT rainbow) + cyan glow + inset white highlight.
- Prompt (Google Fonts) for all UI. JetBrains Mono for hex codes / IDs.
- No emoji in product copy. Outlined 1.5px icons only.
