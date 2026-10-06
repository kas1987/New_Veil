# VEIL Design System

**Core rule:** Ana always dominates. All UI chrome is ghost (`opacity: 0.10`) at rest,
reveals to `opacity: 1` on `:hover` at `0.45s ease`. `#ana-vid` is NEVER ghosted.

---

## Hard Rules (never violate)

- Ghost/reveal: rails/sidebar/footer at `opacity: 0.10`, header at `0.22`, transition `0.45s ease`
- `#ana-vid` is always `z-index: 2`, never ghosted, no `autoplay` attribute
- Typography: `JetBrains Mono` for body/data, `Cinzel` for labels, `Cinzel Decorative` for brand/stats
- All colors via CSS variables — no hardcoded hex outside `:root`
- Boot order: WebGL → `setMood('Dormant')` → video → RAF loop

## Component CSS Templates

### Glass Card
```css
.card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
  padding: 12px;
}
```

### Ghost Rail
```css
.rail {
  opacity: 0.10;
  transition: opacity 0.45s ease;
}
.rail:hover {
  opacity: 1;
}
.rail .card {
  background: transparent;
  backdrop-filter: none;
}
.rail:hover .card {
  background: var(--glass-bg);
  backdrop-filter: blur(8px);
}
```

### Header
```css
.app-header {
  opacity: 0.22;
  transition: opacity 0.45s ease;
}
.app-header:hover {
  opacity: 1;
}
```

## Typography Scale

| Element | Font | Size | Extras |
|---------|------|------|--------|
| Card label / section header | Cinzel | 8.5px | letter-spacing: 0.3em, text-transform: uppercase |
| Stat number / brand wordmark | Cinzel Decorative | ≥17px | — |
| Body / data | JetBrains Mono | 9–11px | — |

## Z-Index Stack

| Element | z-index |
|---------|---------|
| App shell | 1 |
| `#ana-vid` | 2 |
| `#particles` | 999 |
| `#snap-toast` | 9999 |

## Color Tokens (`:root`)

```css
:root {
  --void: #030008;
  --void-light: #0a0a1a;
  --glass-bg: rgba(255, 255, 255, 0.04);
  --glass-border: rgba(255, 255, 255, 0.08);
  --card-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  --text-bright: rgba(255, 255, 255, 0.92);
  --text-muted: rgba(255, 255, 255, 0.45);
  --accent: #a78bfa;
  --accent-glow: 0 0 12px rgba(167, 139, 250, 0.3);
}
```

## Video Rules (`#ana-vid`)

- NO `autoplay` attribute — JS boot sequence controls playback
- Attributes: `muted loop playsinline preload="auto"`
- `mix-blend-mode: screen`
- Dashboard holds on first frame for 6s by design

## Mood System Quick Ref

`setMood(mood)` sets a CSS class on the route root. Cascades through custom properties.
Moods: Dormant, Curiosity, Warmth, Trust, Ache, Desire, Obsession, Grief, Fear, Defiance

## Compliance Checklist

- [ ] Every rail/footer/sidebar at `opacity: 0.10` at rest
- [ ] Hover transition is exactly `opacity 0.45s ease`
- [ ] Cards inside ghost containers: `background: transparent; backdrop-filter: none`
- [ ] `#ana-vid` is NEVER ghosted
- [ ] Only JetBrains Mono, Cinzel, Cinzel Decorative used
- [ ] No hardcoded hex outside `:root {}`
- [ ] Background is `--void` based
- [ ] `#ana-vid` at `z-index: 2`
- [ ] No `autoplay` on `#ana-vid`
- [ ] Interactive elements have visible focus states
- [ ] Buttons use `<button>` not `<div onclick>`
- [ ] No `setInterval` under 100ms

## See Also

- `references/css-variables.md` — Full token set
- `references/component-patterns.md` — Glass card, rail, button templates
- `references/mood-system.md` — Mood-reactive colors and cascade
- `references/js-patterns.md` — Boot sequence, RAF loop
- `references/scaffolding-guide.md` — New page HTML skeleton
- `references/webgl-video-overlay.md` — Video/WebGL layer stack
- `references/metachromatic-bridge.md` — Ops vs narrative surface routing; token map to `07_ui/metachromatic_design_system/`
