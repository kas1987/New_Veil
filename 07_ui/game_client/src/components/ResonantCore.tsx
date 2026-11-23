import type { CueType } from '../lib/resonanceEvaluator'

interface ResonantCoreProps {
  resonance: number
  tierName: string
  veilState: string
  cueType: CueType | null
}

function tierClass(resonance: number): string {
  if (resonance <= 0) return 'core-suffocating core-sealed'
  if (resonance < 100) return 'core-suffocating'
  if (resonance < 350) return 'core-surface'
  if (resonance < 550) return 'core-first-light'
  if (resonance < 850) return 'core-listener'
  return 'core-awakened'
}

function cueClass(cueType: CueType | null): string {
  if (cueType === 'breakthrough_surge') return 'cue-breakthrough'
  if (cueType === 'saturation_cap') return 'cue-bloom'
  if (cueType === 'trust_rupture') return 'cue-rupture'
  if (cueType === 'friction_damping') return 'cue-friction'
  return ''
}

export function ResonantCore({ resonance, tierName, veilState, cueType }: ResonantCoreProps) {
  const norm = Math.max(0, Math.min(1, resonance / 1000))
  const circumference = 2 * Math.PI * 13
  const dashOffset = Number((circumference * (1 - norm)).toFixed(2))
  const label = `Resonant Core: ${tierName} (${veilState.replace('_', ' ')})`

  return (
    <span
      className={`resonant-core ${tierClass(resonance)} ${cueClass(cueType)}`}
      role="img"
      aria-label={label}
      title={label}
    >
      <svg width="26" height="26" viewBox="0 0 36 36" aria-hidden="true">
        <circle className="core-track" cx="18" cy="18" r="13" fill="none" strokeWidth="2.5" />
        <circle
          className="core-ring"
          cx="18"
          cy="18"
          r="13"
          fill="none"
          strokeWidth="2.75"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform="rotate(-90 18 18)"
        />
        <circle className="core-seed" cx="18" cy="18" r={3 + norm * 3.5} />
      </svg>
    </span>
  )
}
