import React, { useId, useMemo } from 'react'

export interface RoadThresholdWaveProps {
  roadName: string
  currentResonance: number // 0.0 to 1000.0
  requiredResonance: number // e.g., 550.0 for Listening Wall
  showNumericRule?: boolean
}

function generateSinePath(
  width: number,
  height: number,
  amplitude: number,
  frequency: number,
  phase = 0,
): string {
  const midY = height / 2
  const points: string[] = []
  for (let x = 0; x <= width; x += 4) {
    const normalizedX = x / width
    const envelope = Math.sin(normalizedX * Math.PI)
    const y = midY + Math.sin(normalizedX * Math.PI * 2 * frequency + phase) * amplitude * envelope
    points.push(`${x === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`)
  }
  return points.join(' ')
}

export const RoadThresholdWave: React.FC<RoadThresholdWaveProps> = ({
  roadName,
  currentResonance,
  requiredResonance,
  showNumericRule = true,
}) => {
  const filterId = useId()
  const isLocked = currentResonance < requiredResonance
  const isSuffocating = currentResonance < 100.0

  const { targetPath, playerPath } = useMemo(() => {
    const w = 280
    const h = 68
    const reqNorm = Math.max(0, Math.min(1, requiredResonance / 1000))
    const curNorm = Math.max(0, Math.min(1, currentResonance / 1000))
    const tFreq = 2 + reqNorm * 5
    const tAmp = 10 + reqNorm * 16
    const pFreq = 2 + curNorm * 5
    const pAmp = 4 + curNorm * 16

    return {
      targetPath: generateSinePath(w, h, tAmp, tFreq, 0),
      playerPath: generateSinePath(w, h, pAmp, pFreq, isLocked ? 1.1 : 0),
    }
  }, [currentResonance, requiredResonance, isLocked])

  return (
    <div className="card" style={{ padding: 12 }}>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: 10,
          fontFamily: 'Cinzel, serif',
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          marginBottom: 6,
        }}
      >
        <span style={{ color: 'var(--text-dim)' }}>{roadName}</span>
        <span
          style={{
            color: isSuffocating
              ? 'var(--text-muted)'
              : isLocked
                ? 'var(--star)'
                : 'var(--emerald)',
          }}
        >
          {isSuffocating ? 'Membrane Suffocating' : isLocked ? 'Frequency Mismatch' : 'Phase Locked'}
        </span>
      </div>

      <svg viewBox="0 0 280 68" style={{ width: '100%', height: 64, overflow: 'visible' }}>
        <defs>
          <filter id={filterId} x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>
        <path
          d={targetPath}
          fill="none"
          stroke="rgba(253, 230, 138, 0.50)"
          strokeWidth="1.75"
          strokeDasharray={isLocked ? '4 4' : 'none'}
        />
        <path
          d={playerPath}
          fill="none"
          stroke={isSuffocating ? '#64748b' : isLocked ? '#22d3ee' : '#34d399'}
          strokeWidth="2.4"
          filter={`url(#${filterId})`}
        />
      </svg>

      {showNumericRule && isLocked && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            borderTop: '1px solid var(--glass-border)',
            paddingTop: 6,
            marginTop: 4,
            fontSize: 11,
            color: 'var(--text-dim)',
          }}
        >
          <span>
            {isSuffocating ? 'The mist turns back toward the Plaza.' : 'The barrier repels your wave.'}
          </span>
          <span>
            Req {requiredResonance.toFixed(1)} / Cur {currentResonance.toFixed(1)}
          </span>
        </div>
      )}
    </div>
  )
}
