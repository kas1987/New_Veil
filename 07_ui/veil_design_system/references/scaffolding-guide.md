# VEIL Page Scaffolding Guide

How to build a new VEIL page from scratch. Follow this skeleton and required-element checklist.

---

## Required HTML Elements

Every VEIL page must have these IDs in exactly this structural order:

```
#cosmic-bg       → WebGL canvas, z-index 0
#ana-vid         → Ana video, z-index 2, mix-blend-mode: screen
#glow-ring       → Mood-reactive gradient ring, behind UI
#particles       → Burst particle layer, z-index 999
.app             → Glass UI shell, z-index 1
  #mood-pill     → Current mood label, clickable to cycle
  #snap-toast    → Toast notification, z-index 9999
```

---

## Minimal HTML Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title | VEIL</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Cinzel+Decorative:wght@400;700&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
  <style>
    /* VEIL tokens inline or via <link> */
    :root {
      --void:         #030008;
      --veil:         #7c3aed;
      --veil-bright:  #a855f7;
      --veil-glow:    rgba(124,58,237,0.45);
      --quasar:       #06b6d4;
      --quasar-bright:#22d3ee;
      --bloom:        #e879f9;
      --star:         #fde68a;
      --emerald:      #34d399;
      --glass-bg:     rgba(10,3,24,0.68);
      --glass-border: rgba(124,58,237,0.20);
      --card-shadow:  0 0 28px rgba(124,58,237,0.10), 0 0 56px rgba(6,182,212,0.05);
    }
  </style>
</head>
<body>

  <!-- Layer 0: WebGL cosmic background -->
  <canvas id="cosmic-bg" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none;"></canvas>

  <!-- Layer 2: Ana video — NEVER ghost, NEVER autoplay -->
  <video id="ana-vid"
    src="ana-florence.mp4"
    style="position:fixed;top:0;left:0;width:100%;height:100%;
           object-fit:cover;pointer-events:none;z-index:2;
           mix-blend-mode:screen;opacity:0.22;
           transition:opacity 1.4s ease,filter 1.4s ease;"
    muted loop playsinline preload="auto"
    aria-label="Ana ambient figure">
  </video>

  <!-- Mood glow ring (behind .app) -->
  <div id="glow-ring" style="position:fixed;inset:0;z-index:0;pointer-events:none;opacity:0.22;transition:all 1.2s ease;"></div>

  <!-- Layer 999: Particle burst -->
  <canvas id="particles" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:999;pointer-events:none;"></canvas>

  <!-- Layer 1: App UI shell -->
  <div class="app" style="position:relative;z-index:1;min-height:100vh;">

    <!-- Mood pill -->
    <div id="mood-pill" onclick="cycleMood()" style="cursor:pointer;">⊙ DORMANT</div>

    <!-- Page content here -->

    <!-- Toast (z-index 9999) -->
    <div id="snap-toast" style="position:fixed;bottom:1.5rem;left:50%;transform:translateX(-50%);z-index:9999;display:none;"></div>

  </div>

  <script src="app.js"></script>
</body>
</html>
```

---

## Required `<link>` and `<script>` Load Order

```html
<!-- 1. Google Fonts (Cinzel, Cinzel Decorative, JetBrains Mono) -->
<!-- 2. VEIL token CSS / inline :root block -->
<!-- 3. Page-specific CSS -->
<!-- 4. External libs (if any) — Lucide, Mermaid, etc. -->
<!-- 5. app.js (bottom of body, after all DOM) -->
```

Never load `app.js` in `<head>` — the boot sequence requires DOM elements to exist.

---

## JS Boot Sequence

In `app.js`, run exactly in this order inside `DOMContentLoaded`:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  initWebGL()        // 1. WebGL canvas setup + shader compile
  setMood('Dormant') // 2. Initial mood — sets video opacity + glow ring
  initParticles?.()  // 3. Particle canvas (optional)
  initVideoBoot()    // 4. Video: hold frame 6s, then drift at Dormant rate
  initAudio?.()      // 5. Web Audio analyser (requires user gesture)

  document.addEventListener('keydown', e => {
    if (e.key === 'm' || e.key === 'M') cycleMood()
  })

  rafLoop()          // 6. Start RAF loop LAST
})
```

**Wrong order** → video starts full-opacity, or RAF runs with zero uniforms.

---

## Ghost/Reveal Required Elements

All UI chrome around Ana must use ghost/reveal. `#ana-vid` never ghosts.

```css
/* Rails / sidebar / footer */
.rail, footer, aside {
  opacity: 0.10;
  transition: opacity 0.45s ease;
}
.rail:hover, footer:hover, aside:hover { opacity: 1; }

/* Header (slightly more visible) */
header {
  opacity: 0.22;
  transition: opacity 0.45s ease;
}
header:hover { opacity: 1; }

/* Cards inside ghost containers — transparent at rest */
.rail .card {
  background: transparent;
  backdrop-filter: none;
  border-color: transparent;
  box-shadow: none;
  transition: background 0.45s ease, backdrop-filter 0.45s ease,
              border-color 0.45s ease, box-shadow 0.45s ease;
}
.rail:hover .card {
  background: var(--glass-bg);
  backdrop-filter: blur(22px);
  border-color: var(--glass-border);
  box-shadow: var(--card-shadow);
}
```

---

## Z-Index Reference

| z-index | Element |
|---------|---------|
| 0 | `#cosmic-bg` WebGL canvas + `#glow-ring` |
| 1 | `.app` UI shell |
| 2 | `#ana-vid` — **never** below 2 |
| 999 | `#particles` burst layer |
| 9999 | `#snap-toast` notifications |

---

## Pre-flight Checklist (new page)

- [ ] `#cosmic-bg` canvas exists, `z-index: 0`
- [ ] `#ana-vid` has `muted loop playsinline preload="auto"` — no `autoplay`
- [ ] `#ana-vid` has `mix-blend-mode: screen` and `z-index: 2`
- [ ] `#glow-ring` exists for mood-reactive background
- [ ] `#snap-toast` at `z-index: 9999`
- [ ] All rail/footer/sidebar have `opacity: 0.10` + `0.45s ease` transition
- [ ] Header has `opacity: 0.22`
- [ ] No `Inter`, `Roboto`, or `system-ui` font families used
- [ ] All colors reference `var(--*)` tokens, no hardcoded hex outside `:root`
- [ ] Boot sequence in correct order (WebGL → mood → video → RAF)
- [ ] `rafLoop()` called last in `DOMContentLoaded`

---

## See Also

- `references/webgl-video-overlay.md` — WebGL shader setup and video layer details
- `references/mood-system.md` — full `setMood()` implementation and all mood tables
- `references/js-patterns.md` — boot sequence, RAF loop, audio reactivity
- `references/component-patterns.md` — glass card, rail, button, stat cell templates
