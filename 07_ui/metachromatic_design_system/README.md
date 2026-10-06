# MetaChromatic Design System

> Bold, futuristic dark-mode mobile app for dynamic color-theming and palette management. Chromatic systems meet frosted glass.

MetaChromatic is a mobile-first product aimed at designers, developers, and artists who need to generate, customize, and sync chromatic color systems across projects and brand assets. Its visual language is dark-mode-first: deep navy/near-black backgrounds carry the UI weight while the brand's prismatic spectrum (blue → cyan → purple → magenta → rose → orange → yellow → green) shifts live with the active palette. Glass panels, cyan glows, and cubic-bezier spring easing define the feel.

## Sources

This design system was reverse-engineered from:

- **Design token repo** — `github.com/kas1987/04-Prism`
  - `design/tokens/metachromatic-tokens.css` — brand palette, glass vars, spacing, transitions
  - `design/tokens/metachromatic-glass.css` — glass surface utility classes + prismatic effects
  - `design/icons/` — logo PNGs (16–1024px) + SVG masters
- **Product codebase** — `github.com/kas1987/Image-Prism`
  - `apps/metachromatic-mobile/` — React + Tailwind mobile PWA (ModelGallery, Generator, NavBar, Lightbox, etc.)
  - `PRODUCT.md`, `METACHROMATIC-MOBILE-SETUP.md` — product overview and mobile app wiring

Neither repo is pre-loaded — the files in `assets/` and the token structures in `colors_and_type.css` are what was extracted. The shipping app is Electron + React (desktop) + a Vite mobile companion; this system models the **mobile** surface.

---

## Index

| File / Folder | What's in it |
|---|---|
| `README.md` | This file — brand overview, content voice, visual foundations, iconography, caveats. |
| `colors_and_type.css` | All design tokens — colors, type scale, glass system, shadows, radii, spacing, transitions. Plus `.mc-h1`/`.mc-body`/etc semantic classes. |
| `assets/` | Logo PNGs (16/32/180/192/512/1024), master + favicon SVG. |
| `fonts/` | Empty — Prompt (display/body) + JetBrains Mono (code/mono) load from Google Fonts. No local files needed. |
| `preview/` | 19 HTML specimen cards, one concept per card, shown in the Design System tab. |
| `preview/brand-logo.html` | 3D faceted gem mark + logotype + size ladder. |
| `preview/live-theming.html` | Interactive hue-scrubber that retunes every token live. |
| `preview/colors-*.html` | Navy/base, prismatic accents, semantic, gradient token sets. |
| `preview/type-*.html` | Display scale, body/label/mono specimens, type effects. |
| `preview/buttons.html` | Primary, secondary, ghost, danger — all states. |
| `preview/cards.html` | Glass card variants. |
| `preview/inputs.html` | Text, textarea, select — default/focus/error. |
| `preview/badges.html` | Tier badges, status pills, labels. |
| `preview/navbar.html` | 7-tab bottom nav. |
| `preview/glass-surfaces.html` | 4-tier blur+tint glass recipe system. |
| `preview/shadows.html` | Elevation + colored glow system. |
| `preview/spacing.html` | 4–80 px spacing scale. |
| `preview/radii.html` | Border-radius token ladder. |
| `preview/progress.html` | Progress bar, skeleton, spinner. |
| `ui_kits/mobile/` | React recreation of the MetaChromatic mobile app — Generator, ModelGallery, ReviewQueue, NavBar, Primitives, IOSDevice frame. Open `index.html`. |
| `SKILL.md` | Agent-skill manifest — load this in Claude Code to design on-brand. |

---

## Content fundamentals

**Voice:** confident, creative, technical. Written for people who care about hex codes and kerning. Short, declarative, and a little understated — the app trusts the color to do the talking.

**Tone:** second-person ("Describe what you want to generate…"), imperative for actions ("Generate", "Export", "Reload"), and neutral for states ("No models match", "Queued", "Running…"). No exclamation marks in normal UI copy. No marketing enthusiasm.

**Casing:**
- **Buttons & nav labels:** Title Case, one word where possible — `Models`, `Generate`, `Review`, `Export`.
- **Section headings & H1s:** Title Case, short — `Models`, `Generate`, `Character`.
- **Inline labels:** lowercase sentence case — `Positive prompt`, `Negative prompt`, `Checkpoint`.
- **Uppercase micro-labels:** letterspaced `.08em` for tag-like metadata (`S+`, `A`, `UNSCORED`).

**Tense & person:** Present tense. The UI speaks *to* the user, not about itself — prefer "Describe what you want…" over "The user should describe…". Avoid "I" entirely.

**Emoji:** **Not used in product UI.** The mobile codebase does currently reach for unicode glyphs (`⊞`, `🖼`, `✦`, `🏷`, `✓`, `⇪`, `♫`) in the NavBar as temporary icon stand-ins — these should be replaced with real outlined SVG glyphs. Brand copy, headings, and toasts are emoji-free.

**Numbers:** Always exact. `832 × 1216 · Pony XL`. `1000+ models (virtualized grid)`. Use `·` (middot) as a separator in secondary metadata rows. Sizes, counts, and progress always render as digits (`12 available`, not "twelve").

**Ellipsis:** horizontal ellipsis character `…`, not three periods. Used for in-progress states (`Generating…`, `Checking…`) and placeholder text (`Search models…`).

**Examples of on-brand copy:**
- `Models` · `24 available`
- `Describe what you want to generate…`
- `✦  Generate`
- `832 × 1216 · Pony XL`
- `No models match "violet"`
- `Failed: connection refused`

---

## Visual foundations

### Motif: dark navy + prismatic arc
The brand hinges on **deep navy + white text + a single chromatic accent that shifts**. The logo is a prismatic arch (rainbow → from blue through to green); the app treats this spectrum as a shared palette across every product area. Cool-biased tints dominate the chrome (cyan cast in radial gradients, purple in corners); warm colors appear as data or status.

### Color
- **Backgrounds:** `#050812` app base → `#0a0e1a` navy surface → `#141a2e` raised → `#1e2842` elevated. Never pure black; always navy-tinted.
- **Foreground:** white at 95 / 65 / 40 / 20% opacity for primary/secondary/muted/disabled. This is a *white-on-navy* system, not a gray-scale system — all fg values are `rgba(255,255,255, x)`.
- **Accent:** cyan `#06b6d4` is the default (status dots, focus rings, active tabs, cyan glow). The "active palette" is user-configurable, so the accent is a variable that swaps through the prismatic spectrum.
- **Gradients:** one principal prismatic gradient (`--mc-gradient-prismatic`) used sparingly — borders, logo, hero moments. The **primary button** gradient is a cool cyan→teal (`135deg, #06b6d4 → #0e7490`), NOT the rainbow.

### Type
- **Display/body:** Prompt (Google Fonts). Geometric, slightly technical, 300/400/500/600/700.
- **Mono:** JetBrains Mono — hex codes, prompt text, numeric IDs.
- **Scale:** 12/14/16/18/20/24/30/36/48/64 px, `rem`-based.
- **Letter-spacing:** tight on display (`-0.03em`), neutral on body, `+0.08em` uppercase on micro labels.
- **Text glow:** cyan text-shadow on active / focus / headline moments: `0 0 20px rgba(6,182,212,0.45)`.

### Backgrounds
Full-bleed radial gradients layered on navy — cyan top-left, violet bottom-right, subtle teal center. Always `background-attachment: fixed`. No textures, no grain, no imagery behind UI chrome. User-provided images (model thumbnails, generated outputs) are the only raster content.

### Spacing & layout
4-based scale (4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64). Screens are **generous** — 16–20 px edge padding on mobile, 24–32 px between major sections. Bottom nav is `64px + safe-area-inset-bottom`. Sticky search bars under titles. Content scrolls under a fixed bottom nav, padded `pb-16`.

### Corner radii
**Medium-biased.** Tokens:
- `4px` — tags, pills, dots
- `8px` — inputs, small buttons
- `12px` — buttons, list rows
- `16px` — cards, panels (the default)
- `24px` — large cards, modals
- `32px` — sheets
- `9999px` — status pills, progress tracks

### Cards
Glass-first: translucent white or navy (`rgba(255,255,255,0.04)` / `rgba(10,14,26,0.65)`) + `backdrop-filter: blur(16–24px)` + 1px `rgba(255,255,255,0.08)` border + `0 8px 32px rgba(0,0,0,0.37)` shadow. No solid-fill cards. On hover, border lightens to `0.15`, card lifts `translateY(-2px)`, shadow deepens.

### Hover / press
- **Hover:** border opacity rises from `.08` → `.15`; sometimes adds a matching colored glow (`mc-glow-cyan`).
- **Press/active:** `transform: scale(0.98)`, background opacity steps up (`.04` → `.09` → `.12`), opacity drops slightly on primary buttons (`0.82`). Never shrink more than 2%.
- **Focus:** 2px cyan ring + inset cyan glow on inputs.
- **Disabled:** opacity `0.32`, shadow removed.

### Borders, shadows, elevation
- **Borders:** always 1px, always white at low opacity (`0.08` → `0.15` → `0.22`). Never colored borders for structure — colored borders ONLY as data-encoding (score tiers, semantic state).
- **Shadows:** three levels (sm/md/lg) plus a **glow** tier for interactive emphasis. Shadows are deep-black `rgba(0,0,0,0.25–0.50)` — do the heavy lifting on the dark background.
- **Inner glow:** inputs get inset cyan on focus; primary buttons get `inset 0 1px 0 rgba(255,255,255,0.15)` for lift.

### Transparency & blur
Central to the identity. `backdrop-filter: blur()` at **four levels**: 8/16/24/40 px. Always paired with `saturate(180–200%)` for richness. Used on cards, nav, modals, sticky headers. NEVER on text containers where legibility matters.

### Animation
- **Durations:** 150 / 250 / 400 ms (fast / normal / slow), plus 500 ms spring for delightful moments.
- **Easing:** `ease` for most; `cubic-bezier(0.34, 1.56, 0.64, 1)` (slight overshoot) for spring.
- **Signature moves:** animated gradient border shimmer (`mc-prismatic-shift` 4 s infinite ease), progress-bar glow-fill, shimmer-skeleton loaders.
- **Motion respect:** `@media (prefers-reduced-motion: reduce)` forces 0.01 ms everywhere.

### Imagery
Cool, high-contrast, dark-friendly. User models/outputs are rendered edge-to-edge in cards with a `bg-gradient-to-t from-black/70 to-transparent` overlay at the bottom so name tags stay legible. No grain, no filters; color saturation as-shot.

### Layout rules (fixed)
- Bottom nav is always fixed, 7 slots, bottom-inset-safe.
- Primary headers sit top-left with an `·` metadata subtitle.
- Search is sticky under the header, blurred.
- Primary action button is a full-width 56 px gradient pill, 2xl radius.

---

## Iconography

**Current state in codebase:** the mobile app uses unicode glyphs (`⊞ 🖼 ✦ 🏷 ✓ ⇪ ♫`) as placeholders. No icon font / sprite is imported. These ship today but are considered tech-debt.

**Canonical direction (documented here):**
- **Style:** minimal, outlined, 1.5 px stroke, 24×24 viewbox, rounded line-caps. Iconography recedes so the color system can lead.
- **Fill vs stroke:** stroked by default; solid-filled only for the brand sparkle (`✦`) and for semantic status dots.
- **Substitute set (FLAG):** **Lucide Icons** is the closest match to the intended style. Loaded via CDN:
  ```html
  <script src="https://unpkg.com/lucide@latest"></script>
  <!-- then <i data-lucide="palette"></i> -->
  ```
- **Emoji:** not used in UI. Unicode glyphs (star, check, arrow) appear only as tech-debt placeholders — treat as bugs.
- **Brand marks:** the prismatic M is the hero icon and lives in `assets/metachromatic-icon.svg` + PNG exports from 16 to 1024.
- **Status dots:** 6 px solid circle + colored `box-shadow` glow (emerald for OK, red for fail, gray for unknown). See NavBar component.

**FLAG to user:** if you have a bespoke icon set, please attach it — Lucide is a stand-in and the codebase currently uses temporary unicode glyphs.

---

## Type stack

**Prompt** (display & body) and **JetBrains Mono** (code, hex, IDs) are the official typefaces — both loaded from Google Fonts via `@import` in `colors_and_type.css`. No local font files required; nothing to license.

---

## Caveats

- Mobile-first coverage only (the desktop Electron app `apps/metachromatic` has similar tokens but wasn't explored in depth).
- Icon set is documented-as-intended, not imported — Lucide is a substitute for the real thing.
