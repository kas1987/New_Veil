# VEIL CSS Variables Reference

Full `:root` token system. All UI should use these variables — never hardcode colors.

```css
:root {
  /* ── Core palette ─────────────────────────────────────────── */
  --void:          #030008;              /* True black background */
  --veil:          #7c3aed;              /* Primary purple */
  --veil-bright:   #a855f7;             /* Lighter purple */
  --veil-glow:     rgba(124,58,237,0.45);
  --quasar:        #06b6d4;             /* Cyan accent */
  --quasar-bright: #22d3ee;
  --quasar-glow:   rgba(6,182,212,0.45);
  --bloom:         #e879f9;             /* Magenta/pink highlight */
  --bloom-glow:    rgba(232,121,249,0.45);
  --star:          #fde68a;             /* Warm amber/gold */
  --emerald:       #34d399;             /* Success / active state */

  /* ── Text scale ───────────────────────────────────────────── */
  --text:          #e2e8f0;             /* Primary text */
  --text-dim:      #94a3b8;             /* Secondary text */
  --text-muted:    #4b5563;             /* Tertiary / labels */

  /* ── Glass system ─────────────────────────────────────────── */
  --glass-bg:      rgba(10,3,24,0.68);
  --glass-border:  rgba(124,58,237,0.20);
  --card-shadow:   0 0 28px rgba(124,58,237,0.10),
                   0 0 56px rgba(6,182,212,0.05);
}
```

## Usage Guidelines

| Token | Use for |
|-------|---------|
| `--void` | Body background, darkest fills |
| `--veil` / `--veil-bright` | Primary interactive elements, LLM indicators |
| `--quasar` / `--quasar-bright` | TTS/audio indicators, secondary accents |
| `--bloom` | Emotional peak moments, Bloom invoke, Responding mood |
| `--star` | Standby/fallback indicators, warm accents |
| `--emerald` | Active/online status, success states |
| `--glass-bg` | Card backgrounds (with backdrop-filter) |
| `--glass-border` | Card/panel borders |
| `--card-shadow` | Card drop shadows |

## Mood Color Mapping

| Mood | Primary Color | Secondary |
|------|--------------|-----------|
| Dormant | `--veil` (dim) | void |
| Listening | `--quasar` | `#0ea5e9` |
| Processing | `#f97316` (orange) | `#ef4444` (red) |
| Responding | `--bloom` | `--quasar` |
| Dissolving | `--veil` (dim) | `#4c1d95` |
