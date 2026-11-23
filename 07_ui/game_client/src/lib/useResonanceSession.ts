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
      const direct = applyDirectDelta(session, source)
      if (direct.appliedDelta === 0 || direct.nextState.isSealedOut) {
        setSession(direct.nextState)
        return direct
      }
      const drifted = processNonTalkTurn(direct.nextState)
      setSession(drifted.nextState)
      return {
        nextState: drifted.nextState,
        appliedDelta: Number((drifted.nextState.resonance - session.resonance).toFixed(2)),
      }
    },
    [session],
  )

  const membrane: VisualMembraneProps = useMemo(() => {
    const r = session.resonance
    const norm = Math.max(0, Math.min(1, r / 1000))

    let tierName = 'First Light'
    if (r < 350) tierName = 'Surface Walker'
    else if (r < 550) tierName = 'First Light'
    else if (r < 750) tierName = 'Veil Listener'
    else if (r < 850) tierName = 'Quasar Tested'
    else tierName = 'Awakened'

    const maskRadius = Math.round(28 + norm * 64)
    const smokeThickness = Number((0.95 - norm * 0.83).toFixed(2))
    const smokeSpill = Math.round(2 + norm * 26)
    const waveFreq = Number((0.5 + norm * 3.5).toFixed(2))

    let hueShift = '210deg'
    if (r < 100) hueShift = '0deg'
    else if (r < 350) hueShift = '215deg'
    else if (r < 750) hueShift = '190deg'
    else hueShift = '42deg'

    return {
      tierName,
      percentDisplay: `${r.toFixed(1)} / 1000`,
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
