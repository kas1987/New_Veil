# VEIL JavaScript Patterns Reference

JS-side patterns for VEIL builds: mood system, WebGL uniforms, boot sequence, audio reactivity, and state management.

---

## State Object (S)

All runtime state lives in a single object to avoid global variable sprawl.

```javascript
const S = {
  mood: 'Dormant',
  targetArousal: 0.20,
  arousal: 0.20,
  valence: 0.0,
  autoTimers: [],
  gl: null,
  glProgram: null,
  glUniforms: {},
  rafId: null,
}
```

---

## Mood Data Tables

```javascript
const MOODS = {
  Dormant:    { arousal: 0.20, valence:  0.0, speed: '36s', label: '⊙ DORMANT'    },
  Listening:  { arousal: 0.42, valence:  0.1, speed: '22s', label: '◎ LISTENING'  },
  Processing: { arousal: 0.64, valence: -0.2, speed: '14s', label: '◉ PROCESSING' },
  Responding: { arousal: 0.90, valence:  0.5, speed:  '8s', label: '⊕ RESPONDING' },
  Dissolving: { arousal: 0.28, valence:  0.0, speed: '28s', label: '⊗ DISSOLVING' },
}
const MOOD_ORDER = ['Dormant', 'Listening', 'Processing', 'Responding', 'Dissolving']

const VID_MOODS = {
  Dormant:    { op: 0.22, rate: 0.25, filter: 'saturate(0.25) brightness(0.45)' },
  Listening:  { op: 0.65, rate: 0.40, filter: 'hue-rotate(175deg) saturate(1.5) brightness(0.95)' },
  Processing: { op: 0.90, rate: 0.70, filter: 'saturate(1.8) brightness(1.15)' },
  Responding: { op: 1.00, rate: 1.10, filter: 'saturate(2.2) brightness(1.25) hue-rotate(18deg)' },
  Dissolving: { op: 0.32, rate: 0.20, filter: 'hue-rotate(245deg) saturate(0.65) brightness(0.55)' },
}

const MOOD_RING = {
  Dormant:    { bg: 'radial-gradient(ellipse at 50% 40%, #2d1060 0%, transparent 68%)', op: 0.22 },
  Listening:  { bg: 'radial-gradient(ellipse at 50% 40%, #06b6d4 0%, #0ea5e9 35%, transparent 72%)', op: 0.36 },
  Processing: { bg: 'radial-gradient(ellipse at 50% 40%, #f97316 0%, #ef4444 35%, transparent 72%)', op: 0.44 },
  Responding: { bg: 'radial-gradient(ellipse at 50% 40%, #e879f9 0%, #22d3ee 30%, #fde68a 58%, transparent 82%)', op: 0.58 },
  Dissolving: { bg: 'radial-gradient(ellipse at 50% 40%, #7c3aed 0%, transparent 68%)', op: 0.24 },
}

const MOOD_ELEMENT = {
  Dormant: 'void silence', Listening: 'ocean current',
  Processing: 'solar fire', Responding: 'prismatic burst', Dissolving: 'fading veil',
}
```

---

## setMood() — Full Implementation

```javascript
function setMood(name) {
  S.autoTimers.forEach(clearTimeout); S.autoTimers = []
  S.mood = name
  S.targetArousal = MOODS[name].arousal

  // Mood pill label
  const pill = document.getElementById('mood-pill')
  if (pill) pill.textContent = MOODS[name].label

  // Glow ring
  const ring = MOOD_RING[name] || MOOD_RING.Dormant
  const grEl = document.getElementById('glow-ring')
  if (grEl) { grEl.style.background = ring.bg; grEl.style.opacity = ring.op }

  // Tagline
  const tlEl = document.getElementById('persona-tagline-el')
  if (tlEl) tlEl.textContent = MOOD_ELEMENT[name] || 'void silence'

  // Responding → Dissolving → Dormant cascade
  if (name === 'Responding') S.autoTimers.push(setTimeout(() => setMood('Dissolving'), 3200))
  if (name === 'Dissolving') S.autoTimers.push(setTimeout(() => setMood('Dormant'),    4500))

  // Ana video
  const vid = document.getElementById('ana-vid')
  if (vid) {
    const vm = VID_MOODS[name] || VID_MOODS.Dormant
    vid.style.opacity = vm.op
    vid.style.filter  = vm.filter
    try { vid.playbackRate = vm.rate } catch (_) {}
  }
}

function cycleMood() {
  const idx = MOOD_ORDER.indexOf(S.mood)
  setMood(MOOD_ORDER[(idx + 1) % MOOD_ORDER.length])
}
```

### Mood Cascade Flow

```
invokeBloom()  → setMood('Responding') → [3.2s] → setMood('Dissolving') → [4.5s] → setMood('Dormant')
invokeQuasar() → setMood('Processing') → [on response complete] → setMood('Responding') → [cascade above]
```

---

## WebGL Setup

### Uniforms

| Uniform | Type | Description |
|---------|------|-------------|
| `u_res` | vec2 | Canvas resolution in pixels |
| `u_time` | float | Seconds since page load |
| `u_mouse` | vec2 | Normalized mouse position (0–1) |
| `u_arousal` | float | 0–1, drives energy/intensity |
| `u_valence` | float | -1 to +1, shifts hue warm/cool |

### Initialization Pattern

```javascript
function initWebGL() {
  const canvas = document.getElementById('cosmic-bg')
  const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
  if (!gl) return
  S.gl = gl

  // compile vert + frag shaders, link program...
  // (shader source from webgl-video-overlay.md)

  S.glUniforms = {
    res:     gl.getUniformLocation(S.glProgram, 'u_res'),
    time:    gl.getUniformLocation(S.glProgram, 'u_time'),
    mouse:   gl.getUniformLocation(S.glProgram, 'u_mouse'),
    arousal: gl.getUniformLocation(S.glProgram, 'u_arousal'),
    valence: gl.getUniformLocation(S.glProgram, 'u_valence'),
  }
}
```

### RAF Loop (arousal interpolation + WebGL tick)

```javascript
let _t0 = performance.now()
let _mx = 0.5, _my = 0.5

document.addEventListener('mousemove', e => {
  _mx = e.clientX / window.innerWidth
  _my = 1 - e.clientY / window.innerHeight
})

function rafLoop() {
  S.rafId = requestAnimationFrame(rafLoop)

  // Smooth arousal toward target (lerp)
  S.arousal += (S.targetArousal - S.arousal) * 0.04

  const gl = S.gl
  if (gl && S.glProgram) {
    gl.useProgram(S.glProgram)
    const t = (performance.now() - _t0) / 1000
    gl.uniform2f(S.glUniforms.res, gl.canvas.width, gl.canvas.height)
    gl.uniform1f(S.glUniforms.time, t)
    gl.uniform2f(S.glUniforms.mouse, _mx, _my)
    gl.uniform1f(S.glUniforms.arousal, S.arousal)
    gl.uniform1f(S.glUniforms.valence, S.valence)
    gl.drawArrays(gl.TRIANGLES, 0, 6)
  }

  // Waveform render (if audio active)
  renderWaveform?.()
}
```

---

## Boot Sequence (required order)

```javascript
document.addEventListener('DOMContentLoaded', () => {
  initWebGL()          // 1. WebGL canvas — must be first (z-index 0 layer)
  setMood('Dormant')   // 2. Mood state init — sets video opacity + ring
  initParticles?.()    // 3. Particle burst layer (z-index 999)
  initVideoBoot()      // 4. Video: hold frame, schedule drift start
  initAudio?.()        // 5. Web Audio analyser (optional, after user gesture)

  document.addEventListener('keydown', e => {
    if (e.key === 'm' || e.key === 'M') cycleMood()
  })
  rafLoop()            // 6. Start main loop last
})
```

**Wrong order consequence:** If video boots before `setMood('Dormant')`, video starts at full opacity. If RAF starts before WebGL init, first frame gets zero uniforms.

---

## Video Boot

```javascript
function initVideoBoot() {
  const vid = document.getElementById('ana-vid')
  if (!vid) return
  vid.loop = true
  vid.muted = true
  vid.currentTime = 0
  vid.pause()

  let _driftStarted = false
  const startDrift = () => {
    if (_driftStarted) return
    _driftStarted = true
    vid.playbackRate = VID_MOODS.Dormant.rate  // 0.25
    vid.play().catch(() => {})
  }
  setTimeout(startDrift, 6000)
  document.addEventListener('click', startDrift, { once: true })
}
```

No `autoplay` attribute on `#ana-vid` — this function controls playback timing.

---

## Audio Reactivity (optional)

```javascript
let _analyser, _freqData

async function initAudio() {
  try {
    const ctx = new AudioContext()
    _analyser = ctx.createAnalyser()
    _analyser.fftSize = 256
    _freqData = new Uint8Array(_analyser.frequencyBinCount)
    // Connect microphone or audio element to analyser...
  } catch (_) {}
}

function getAudioArousal() {
  if (!_analyser) return S.targetArousal
  _analyser.getByteFrequencyData(_freqData)
  const bass = _freqData.slice(0, 8).reduce((a, b) => a + b, 0) / (8 * 255)
  return Math.min(1, S.targetArousal + bass * 0.3)
}
```

In RAF loop: `S.arousal += (getAudioArousal() - S.arousal) * 0.04`

---

## Ana Canvas Palette (Procedural Figure)

```javascript
const ANA_PALS = {
  Dormant:    { cols: ['#0d0618','#1e0a3c','#0a0318'], glow: '#2d1060', body: 'rgba(3,1,8,0.90)',    alpha: 0.18, lenM: 0.55 },
  Listening:  { cols: ['#06b6d4','#0ea5e9','#7c3aed'], glow: '#06b6d4', body: 'rgba(2,6,18,0.87)',   alpha: 0.72, lenM: 1.00 },
  Processing: { cols: ['#f97316','#ef4444','#fbbf24'], glow: '#f97316', body: 'rgba(10,2,2,0.88)',   alpha: 0.88, lenM: 1.20 },
  Responding: { cols: ['#e879f9','#22d3ee','#fde68a','#34d399'], glow: '#e879f9', body: 'rgba(5,1,13,0.76)', alpha: 1.00, lenM: 1.35 },
  Dissolving: { cols: ['#7c3aed','#4c1d95','#c026d3'], glow: '#7c3aed', body: 'rgba(6,2,15,0.84)',   alpha: 0.38, lenM: 0.70 },
}
```

Used by `renderAnaFlorence()` on `#ana-canvas`. The MP4 video is primary; this canvas supplements it.

---

## Anti-Patterns

| Pattern | Fix |
|---------|-----|
| Starting RAF before WebGL init | Always call `initWebGL()` first |
| `autoplay` on `#ana-vid` | Use `initVideoBoot()` pattern — JS controls timing |
| Multiple `setMood()` cascades racing | `S.autoTimers.forEach(clearTimeout)` at top of `setMood()` clears previous timers |
| `setInterval` for animation | Use `requestAnimationFrame` — intervals block at throttled tabs |
| Directly mutating `S.arousal` | Set `S.targetArousal`; let RAF lerp smooth it |
| Hard-coding arousal/valence values in draw calls | Keep them in `MOODS` table; drive via `setMood()` |
