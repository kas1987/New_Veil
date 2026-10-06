# WebGL + Video Overlay Architecture

The VEIL visual system uses two layers of full-screen graphics that compose via blend modes.

## Layer Stack

```
z-index 0 — WebGL canvas (#cosmic-bg)
  Custom fragment shader: double counter-rotating domain-warped foil planes
  Drives: warm spectrum (violet/rose/gold) + cool spectrum (teal/cyan/electric)
  Uniforms: u_time, u_mouse, u_arousal, u_valence

z-index 2 — Ana video (#ana-vid)
  mix-blend-mode: screen
  Dark pixels = transparent (WebGL shows through)
  Bright pixels = figure's color composited over WebGL

z-index 1 — .app layout (glass UI chrome above WebGL, below Ana)
```

## HTML Setup

```html
<canvas id="cosmic-bg"></canvas>
<video id="ana-vid"
  src="ana-florence.mp4"
  style="position:fixed;top:0;left:0;width:100%;height:100%;
         object-fit:cover;pointer-events:none;z-index:2;
         mix-blend-mode:screen;opacity:0.22;
         transition:opacity 1.4s ease,filter 1.4s ease;"
  muted loop playsinline preload="auto">
</video>
```

**No `autoplay` attribute** — JS controls playback timing.

## Video Boot Sequence

```javascript
;(function () {
  const vid = document.getElementById('ana-vid')
  if (!vid) return
  vid.loop = true
  vid.muted = true
  // Hold on first frame for ~6 s, then drift into slow Dormant playback
  vid.currentTime = 0
  vid.pause()
  let _driftStarted = false
  const startDrift = () => {
    if (_driftStarted) return
    _driftStarted = true
    vid.playbackRate = VID_MOODS.Dormant.rate   // 0.25
    vid.play().catch(() => {})
  }
  setTimeout(startDrift, 6000)
  document.addEventListener('click', startDrift, { once: true })
})()
```

## VID_MOODS — Mood-Reactive Video Control

```javascript
const VID_MOODS = {
  Dormant:    { op: 0.22, rate: 0.25, filter: 'saturate(0.25) brightness(0.45)' },
  Listening:  { op: 0.65, rate: 0.40, filter: 'hue-rotate(175deg) saturate(1.5) brightness(0.95)' },
  Processing: { op: 0.90, rate: 0.70, filter: 'saturate(1.8) brightness(1.15)' },
  Responding: { op: 1.00, rate: 1.10, filter: 'saturate(2.2) brightness(1.25) hue-rotate(18deg)' },
  Dissolving: { op: 0.32, rate: 0.20, filter: 'hue-rotate(245deg) saturate(0.65) brightness(0.55)' },
}
```

Applied in `setMood()`:
```javascript
const vm = VID_MOODS[name] || VID_MOODS.Dormant
_vid.style.opacity = vm.op
_vid.style.filter  = vm.filter
try { _vid.playbackRate = vm.rate } catch (_) {}
```

## WebGL Uniforms

| Uniform | Type | Description |
|---------|------|-------------|
| `u_res` | vec2 | Canvas resolution in pixels |
| `u_time` | float | Seconds since page load |
| `u_mouse` | vec2 | Normalized mouse position (0–1) |
| `u_arousal` | float | 0–1, drives energy/intensity |
| `u_valence` | float | -1 to +1, shifts hue spectrum |

Mood drives arousal/valence targets; the RAF loop smoothly interpolates toward them.

## Why `mix-blend-mode: screen`

Screen blend mode: `result = 1 - (1-A)*(1-B)`

- Pure black from video (0,0,0) → becomes fully transparent (shows WebGL)
- Pure white from video (1,1,1) → stays white
- The Ana video is shot/rendered as a dark silhouette with bright luminous energy — this makes the dark body transparent while the glowing streams composite beautifully over the cosmic WebGL background

## Canvas + ANA_CTX (Canvas fallback figure)

The dashboard also has a `#ana-canvas` 2D canvas with a procedural figure rendered in JS (`renderAnaFlorence()`). This runs in parallel with the MP4 video. The MP4 is the primary visual; the canvas figure supplements.

## Performance Notes

- WebGL runs in RAF loop alongside waveform rendering
- Ana video uses `will-change: opacity, filter` for GPU-composited transitions
- Bass energy from Web Audio analyser modulates WebGL arousal in real-time
