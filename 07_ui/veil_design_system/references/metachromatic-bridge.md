# MetaChromatic ↔ VEIL Design Bridge

Veil Small Town uses **two complementary design surfaces**. Pick the right one before building UI.

| Surface | System | Path | Use when |
|---------|--------|------|----------|
| **In-world / narrative** | VEIL | `07_ui/veil_design_system/` | Ana shell, ghost/reveal chrome, mood-reactive story UI, `#ana-vid` layer stack |
| **Harness / ops / tooling** | MetaChromatic | `07_ui/metachromatic_design_system/` | Observatory, dashboards, queue inspectors, batch runners, mobile kit prototypes |

## Token mapping (shared concepts)

| Concept | VEIL (`--*`) | MetaChromatic (`--mc-*`) |
|---------|--------------|-------------------------|
| Deepest background | `--void` `#030008` | `--bg-app` `#050812` |
| Glass panel | `--glass-bg` | `--mc-glass-bg` / `--mc-glass-bg-white` |
| Glass border | `--glass-border` | `--mc-glass-border` |
| Primary accent | `--veil` / `--accent` purple | `--mc-cyan` `#06b6d4` (default ops accent) |
| Secondary accent | `--quasar` cyan | `--mc-purple` |
| Body / data mono | JetBrains Mono | JetBrains Mono |
| Display / labels | Cinzel / Cinzel Decorative | Prompt (300–700) |
| Card radius | `12px` | `--mc-radius-md` `16px` |
| Card shadow | `--card-shadow` (purple/cyan glow) | `--mc-shadow` (deep black lift) |

## Rules when mixing

1. **Do not blend typography stacks on one screen.** VEIL screens use Cinzel; MetaChromatic ops screens use Prompt.
2. **Prismatic rainbow gradient** is hero-only in MetaChromatic — never the default button fill (use `--mc-gradient-primary` cyan→teal instead).
3. **Ghost/reveal (`opacity: 0.10` rails)** is VEIL-only — MetaChromatic uses always-visible glass with hover border lift.
4. **Pre-commit hook** blocks Inter/Roboto outside `07_ui/veil_design_system/` — Prompt and JetBrains Mono are allowed.
5. **Gradio Observatory** loads `metachromatic_design_system/veil_observatory_theme.css` (MetaChromatic ops chrome).

## Quick start — MetaChromatic HTML mock

```html
<link rel="stylesheet" href="../metachromatic_design_system/colors_and_type.css">
<body class="mc">
  <h1 class="mc-h1">Veil Town Observatory</h1>
  <p class="mc-body">24 agents · 3 districts unlocked</p>
</body>
```

Preview specimens: open files under `07_ui/metachromatic_design_system/preview/` in a browser.

Mobile React kit: `07_ui/metachromatic_design_system/ui_kits/mobile/index.html`

## Provenance

Extracted from `MetaChromatic Design System.zip` (Downloads, 2026-05-24).  
Upstream sources documented in `07_ui/metachromatic_design_system/README.md` (`04-Prism` tokens + `Image-Prism` mobile app).
