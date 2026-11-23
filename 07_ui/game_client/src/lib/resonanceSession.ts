import {
  evaluateTalkResonance,
  NpcEncounterState,
  ResonanceEvaluation,
} from './resonanceEvaluator'

export type VeilState = 'calm' | 'still' | 'storm' | 'quasar_active'

export interface ResonanceSessionState {
  resonance: number // 0.000 to 1.000
  turnsTaken: number // Accepted talks count
  turnsSinceLastTalk: number // Tracks 3-turn drift intervals
  hasCrossedFirstThreshold: boolean // True once >= 0.450
  veilState: VeilState
  playerLastLine: string
  recentKeywords: string[] // Rolling 2-turn thematic word window
  encounters: Record<string, NpcEncounterState>
  isSealedOut: boolean // True if resonance hits 0.000
}

export interface RoadLockCheck {
  allowed: boolean
  reason?: 'resonance_too_low' | 'veil_state_mismatch' | 'missing_key_item' | 'veil_suffocation_loop'
  requiredResonance?: number
  currentResonance: number
  loopedToPlaza?: boolean
}

const ITEM_DELTAS: Record<string, number> = {
  echo_shard: 0.04,
  vial_of_memory_ash: 0.06,
  ash: 0.06,
}

export function createInitialSession(): ResonanceSessionState {
  return {
    resonance: 0.35,
    turnsTaken: 0,
    turnsSinceLastTalk: 0,
    hasCrossedFirstThreshold: false,
    veilState: 'calm',
    playerLastLine: '',
    recentKeywords: [],
    encounters: {},
    isSealedOut: false,
  }
}

function applyGraceAndClamp(
  candidate: number,
  state: ResonanceSessionState,
): { value: number; sealedOut: boolean } {
  const inGraceWindow = state.turnsTaken < 5 && !state.hasCrossedFirstThreshold
  let next = Number(candidate.toFixed(3))

  if (inGraceWindow && next < 0.35) {
    next = 0.35
  }

  next = Math.max(0.0, Math.min(1.0, next))
  return {
    value: next,
    sealedOut: next === 0.0,
  }
}

export function processTalkTurn(
  state: ResonanceSessionState,
  npcId: string,
  npcLastLine: string,
  playerLine: string,
  defaultStance: NpcEncounterState['currentStance'] = 'guarded',
  relevantUnlockedTokens: string[] = [],
): {
  nextState: ResonanceSessionState
  evaluation: ResonanceEvaluation
  renderedPlayerText: string
} {
  const encounter: NpcEncounterState = state.encounters[npcId] ?? {
    npcId,
    initialStance: defaultStance,
    currentStance: defaultStance,
    turnsSpentInResistance: 0,
    consecutiveAttunedTurns: 0,
    breakthroughAwarded: false,
    relevantUnlockedTokens,
  }

  const renderedPlayerText =
    state.resonance < 0.1 ? corruptLineWithStatic(playerLine, state.resonance) : playerLine

  const evaluation = evaluateTalkResonance(playerLine, {
    currentResonance: state.resonance,
    turnsTaken: state.turnsTaken,
    hasCrossedFirstThreshold: state.hasCrossedFirstThreshold,
    npcLastLine,
    playerLastLine: state.playerLastLine,
    recentKeywords: state.recentKeywords,
    veilState: state.veilState,
    encounter,
  })

  const crossed450 = state.hasCrossedFirstThreshold || evaluation.newResonance >= 0.45

  return {
    evaluation,
    renderedPlayerText,
    nextState: {
      ...state,
      resonance: evaluation.newResonance,
      turnsTaken: state.turnsTaken + 1,
      turnsSinceLastTalk: 0,
      hasCrossedFirstThreshold: crossed450,
      playerLastLine: playerLine,
      encounters: {
        ...state.encounters,
        [npcId]: evaluation.updatedEncounter,
      },
      isSealedOut: evaluation.newResonance === 0.0,
    },
  }
}

export function processNonTalkTurn(state: ResonanceSessionState): {
  nextState: ResonanceSessionState
  driftApplied: number
} {
  const nextIdleCount = state.turnsSinceLastTalk + 1
  let driftApplied = 0

  if (nextIdleCount >= 3) {
    driftApplied = state.veilState === 'storm' ? -0.02 : -0.01
  }

  const { value, sealedOut } = applyGraceAndClamp(state.resonance + driftApplied, state)

  return {
    driftApplied: Number((value - state.resonance).toFixed(3)),
    nextState: {
      ...state,
      resonance: value,
      turnsSinceLastTalk: nextIdleCount >= 3 ? 0 : nextIdleCount,
      isSealedOut: sealedOut,
    },
  }
}

export function applyDirectDelta(
  state: ResonanceSessionState,
  source: { itemId?: string; trialDelta?: number },
): { nextState: ResonanceSessionState; appliedDelta: number } {
  const delta = source.itemId ? (ITEM_DELTAS[source.itemId] ?? 0) : (source.trialDelta ?? 0)
  if (delta === 0) return { nextState: state, appliedDelta: 0 }

  const next = Math.max(0.0, Math.min(1.0, Number((state.resonance + delta).toFixed(3))))
  const crossed450 = state.hasCrossedFirstThreshold || next >= 0.45

  return {
    appliedDelta: Number((next - state.resonance).toFixed(3)),
    nextState: {
      ...state,
      resonance: next,
      hasCrossedFirstThreshold: crossed450,
      isSealedOut: next === 0.0,
    },
  }
}

export function checkRoadAccess(
  state: ResonanceSessionState,
  opts: {
    placeMinResonance?: number
    settlementMinResonance?: number
    requiredVeilStates?: VeilState[]
    hasRequiredKeyItem?: boolean
  },
): RoadLockCheck {
  if (state.resonance < 0.1) {
    return {
      allowed: false,
      reason: 'veil_suffocation_loop',
      currentResonance: state.resonance,
      loopedToPlaza: true,
    }
  }

  const required = Math.max(opts.placeMinResonance ?? 0, opts.settlementMinResonance ?? 0)
  if (required > 0 && state.resonance < required) {
    return {
      allowed: false,
      reason: 'resonance_too_low',
      requiredResonance: required,
      currentResonance: state.resonance,
    }
  }

  if (opts.requiredVeilStates && !opts.requiredVeilStates.includes(state.veilState)) {
    return {
      allowed: false,
      reason: 'veil_state_mismatch',
      currentResonance: state.resonance,
    }
  }

  if (opts.hasRequiredKeyItem === false) {
    return {
      allowed: false,
      reason: 'missing_key_item',
      currentResonance: state.resonance,
    }
  }

  return { allowed: true, currentResonance: state.resonance }
}

function corruptLineWithStatic(line: string, resonance: number): string {
  const dropProbability = Math.max(0.35, 1 - resonance * 8)
  return line
    .split(/\s+/)
    .map((word, idx) => {
      const hash = ((word.charCodeAt(0) || 7) + idx * 13) % 100
      return hash / 100 < dropProbability ? '...' : word
    })
    .join(' ')
}
