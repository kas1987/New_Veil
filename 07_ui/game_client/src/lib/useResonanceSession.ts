import { useCallback, useMemo, useState } from 'react'
import { EncounterStance, ResonanceEvaluation } from './resonanceEvaluator'
import {
  applyDirectDelta,
  createInitialSession,
  processNonTalkTurn,
  processTalkTurn,
  ResonanceSessionState,
} from './resonanceSession'

export interface VisualMembraneProps {
  tierName: string
  percentDisplay: string
  cssVars: {
    '--veil-mask-radius': string
    '--veil-smoke-thickness': string
    '--veil-smoke-spill': string
    '--veil-wave-frequency': string
    '--veil-hue-shift': string
  }
  activeCue: ResonanceEvaluation['cueType'] | null
}

export function useResonanceSession() {
  const [session, setSession] = useState<ResonanceSessionState>(createInitialSession)
  const [lastEvaluation, setLastEvaluation] = useState<ResonanceEvaluation | null>(null)

  const submitTalk = useCallback(
    (
      npcId: string,
      npcLastLine: string,
      playerLine: string,
      defaultStance: EncounterStance = 'guarded',
      relevantUnlockedTokens: string[] = [],
    ) => {
      const result = processTalkTurn(
        session,
        npcId,
        npcLastLine,
        playerLine,
        defaultStance,
        relevantUnlockedTokens,
      )
      setSession(result.nextState)
      setLastEvaluation(result.evaluation)
      return result
    },
    [session],
  )

  const advanceNonTalkTurn = useCallback(() => {
    const result = processNonTalkTurn(session)
    setSession(result.nextState)
    return result
  }, [session])

  const useConsumableOrTrial = useCallback(
    (source: { itemId?: string; trialDelta?: number }) => {
      const result = applyDirectDelta(session, source)
      setSession(result.nextState)
      return result
    },
    [session],
  )

  const membrane: VisualMembraneProps = useMemo(() => {
    const r = session.resonance

    let tierName = 'First Light'
    if (r < 0.35) tierName = 'Surface Walker'
    else if (r < 0.55) tierName = 'First Light'
    else if (r < 0.75) tierName = 'Veil Listener'
    else if (r < 0.85) tierName = 'Quasar Tested'
    else tierName = 'Awakened'

    const maskRadius = Math.round(28 + r * 64)
    const smokeThickness = Number((0.95 - r * 0.83).toFixed(2))
    const smokeSpill = Math.round(2 + r * 26)
    const waveFreq = Number((0.5 + r * 3.5).toFixed(2))

    let hueShift = '210deg'
    if (r < 0.1) hueShift = '0deg'
    else if (r < 0.35) hueShift = '215deg'
    else if (r < 0.75) hueShift = '190deg'
    else hueShift = '42deg'

    return {
      tierName,
      percentDisplay: `${Math.round(r * 100)}%`,
      activeCue: lastEvaluation?.cueType ?? null,
      cssVars: {
        '--veil-mask-radius': `${maskRadius}%`,
        '--veil-smoke-thickness': `${smokeThickness}`,
        '--veil-smoke-spill': `${smokeSpill}px`,
        '--veil-wave-frequency': `${waveFreq}s`,
        '--veil-hue-shift': hueShift,
      },
    }
  }, [session.resonance, lastEvaluation])

  return {
    session,
    lastEvaluation,
    membrane,
    submitTalk,
    advanceNonTalkTurn,
    useConsumableOrTrial,
  }
}
