# VEIL Mood System Reference

Full template for the mood-reactive state system. Copy this pattern to any new VEIL build.

## Five Moods

```javascript
const MOODS = {
  Dormant:    { arousal: 0.20, valence:  0.0, speed: '36s', label: '⊙ DORMANT'    },
  Listening:  { arousal: 0.42, valence:  0.1, speed: '22s', label: '◎ LISTENING'  },
  Processing: { arousal: 0.64, valence: -0.2, speed: '14s', label: '◉ PROCESSING' },
  Responding: { arousal: 0.90, valence:  0.5, speed:  '8s', label: '⊕ RESPONDING' },
  Dissolving: { arousal: 0.28, valence:  0.0, speed: '28s', label: '⊗ DISSOLVING' },
}
const MOOD_ORDER = ['Dormant', 'Listening', 'Processing', 'Responding', 'Dissolving']
```

- `arousal` — WebGL energy level (0–1), also drives sigil/stream intensity
- `valence` — WebGL hue shift (-1 to +1), warm vs cool spectrum
- `speed` — sigil rotation speed (CSS animation-duration)
- `label` — text shown in the mood pill

## Video Mood Parameters

```javascript
const VID_MOODS = {
  Dormant:    { op: 0.22, rate: 0.25, filter: 'saturate(0.25) brightness(0.45)' },
  Listening:  { op: 0.65, rate: 0.40, filter: 'hue-rotate(175deg) saturate(1.5) brightness(0.95)' },
  Processing: { op: 0.90, rate: 0.70, filter: 'saturate(1.8) brightness(1.15)' },
  Responding: { op: 1.00, rate: 1.10, filter: 'saturate(2.2) brightness(1.25) hue-rotate(18deg)' },
  Dissolving: { op: 0.32, rate: 0.20, filter: 'hue-rotate(245deg) saturate(0.65) brightness(0.55)' },
}
```

- `op` — video opacity (0–1)
- `rate` — playbackRate (capped by browser; typical range 0.1–16)
- `filter` — CSS filter applied to video element

## Glow Ring

```javascript
const MOOD_RING = {
  Dormant:    { bg: 'radial-gradient(ellipse at 50% 40%, #2d1060 0%, transparent 68%)', op: 0.22 },
  Listening:  { bg: 'radial-gradient(ellipse at 50% 40%, #06b6d4 0%, #0ea5e9 35%, transparent 72%)', op: 0.36 },
  Processing: { bg: 'radial-gradient(ellipse at 50% 40%, #f97316 0%, #ef4444 35%, transparent 72%)', op: 0.44 },
  Responding: { bg: 'radial-gradient(ellipse at 50% 40%, #e879f9 0%, #22d3ee 30%, #fde68a 58%, transparent 82%)', op: 0.58 },
  Dissolving: { bg: 'radial-gradient(ellipse at 50% 40%, #7c3aed 0%, transparent 68%)', op: 0.24 },
}
```

Applied to `#glow-ring` element: `grEl.style.background = ring.bg; grEl.style.opacity = ring.op`

## Elemental Taglines

```javascript
const MOOD_ELEMENT = {
  Dormant:    'void silence',
  Listening:  'ocean current',
  Processing: 'solar fire',
  Responding: 'prismatic burst',
  Dissolving: 'fading veil',
}
```

## setMood() Implementation

```javascript
function setMood(name) {
  S.autoTimers.forEach(clearTimeout); S.autoTimers = []
  S.mood = name
  S.targetArousal = MOODS[name].arousal

  // Update mood pill label
  document.getElementById('mood-pill').textContent = MOODS[name].label

  // Glow ring
  const ring = MOOD_RING[name] || MOOD_RING.Dormant
  const grEl = document.getElementById('glow-ring')
  if (grEl) { grEl.style.background = ring.bg; grEl.style.opacity = ring.op }

  // Tagline
  const tlEl = document.getElementById('persona-tagline-el')
  if (tlEl) tlEl.textContent = MOOD_ELEMENT[name] || 'void silence'

  // Auto-cascade: Responding → Dissolving → Dormant
  if (name === 'Responding') S.autoTimers.push(setTimeout(() => setMood('Dissolving'), 3200))
  if (name === 'Dissolving') S.autoTimers.push(setTimeout(() => setMood('Dormant'),    4500))

  // Drive Ana video
  const _vid = document.getElementById('ana-vid')
  if (_vid) {
    const vm = VID_MOODS[name] || VID_MOODS.Dormant
    _vid.style.opacity = vm.op
    _vid.style.filter  = vm.filter
    try { _vid.playbackRate = vm.rate } catch (_) {}
  }
}

function cycleMood() {
  const idx = MOOD_ORDER.indexOf(S.mood)
  setMood(MOOD_ORDER[(idx + 1) % MOOD_ORDER.length])
}
```

## Mood Cascade

```
invokeBloom()  → setMood('Responding') → [3.2s] → setMood('Dissolving') → [4.5s] → setMood('Dormant')
invokeQuasar() → setMood('Processing') → [on response] → setMood('Responding') → [cascade above]
```

## Keyboard Shortcut

```javascript
document.addEventListener('keydown', e => {
  if (e.key === 'm' || e.key === 'M') cycleMood()
})
```

Mood pill `onclick="cycleMood()"` also cycles through all five moods in order.

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
