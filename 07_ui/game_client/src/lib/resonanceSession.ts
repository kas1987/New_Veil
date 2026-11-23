import {
  evaluateTalkResonance,
  NpcEncounterState,
  PersonalityWeights,
  ResonanceEvaluation,
} from './resonanceEvaluator'

export type VeilState = 'calm' | 'still' | 'storm' | 'quasar_active'

export interface ResonanceSessionState {
  resonance: number // 0.0 to 1000.0
  turnsTaken: number // Accepted talks count
  turnsSinceLastTalk: number // Tracks 3-turn drift intervals
  hasCrossedFirstThreshold: boolean // True once >= 450.0
  veilState: VeilState
  playerLastLine: string
  recentKeywords: string[] // Flattened rolling 2-turn thematic word window
  keywordHistory?: string[][] // Per-turn thematic word window (last 2 turns)
  encounters: Record<string, NpcEncounterState>
  isSealedOut: boolean // True if resonance hits 0.0
}

export interface RoadLockCheck {
  allowed: boolean
  reason?: 'resonance_too_low' | 'veil_state_mismatch' | 'missing_key_item' | 'veil_suffocation_loop'
  requiredResonance?: number
  currentResonance: number
  loopedToPlaza?: boolean
}

const ITEM_DELTAS: Record<string, number> = {
  echo_shard: 6.0,
  vial_of_memory_ash: 10.0,
  ash: 10.0,
}

export function createInitialSession(): ResonanceSessionState {
  return {
    resonance: 350.0,
    turnsTaken: 0,
    turnsSinceLastTalk: 0,
    hasCrossedFirstThreshold: false,
    veilState: 'calm',
    playerLastLine: '',
    recentKeywords: [],
    keywordHistory: [],
    encounters: {},
    isSealedOut: false,
  }
}

function applyGraceAndClamp(
  candidate: number,
  state: ResonanceSessionState,
): { value: number; sealedOut: boolean } {
  const inGraceWindow = state.turnsTaken < 5 && !state.hasCrossedFirstThreshold
  let next = Number(candidate.toFixed(2))

  if (inGraceWindow && next < 350.0) {
    next = 350.0
  }

  next = Math.max(0.0, Math.min(1000.0, next))
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
  personalityWeights?: PersonalityWeights,
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
    npcBond: 0.0,
    townContribution: 0.0,
  }

  const renderedPlayerText =
    state.resonance < 100.0 ? corruptLineWithStatic(playerLine, state.resonance) : playerLine

  const evaluation = evaluateTalkResonance(playerLine, {
    currentResonance: state.resonance,
    turnsTaken: state.turnsTaken,
    hasCrossedFirstThreshold: state.hasCrossedFirstThreshold,
    npcLastLine,
    playerLastLine: state.playerLastLine,
    recentKeywords: state.recentKeywords,
    veilState: state.veilState,
    encounter,
    personalityWeights,
  })

  const crossed450 = state.hasCrossedFirstThreshold || evaluation.newResonance >= 450.0
  const usedThisTurn = Array.from(
    new Set([
      ...(evaluation.signals.resonantWordsHit ?? []),
      ...(evaluation.signals.fatiguedWords ?? []),
    ]),
  )
  const prevHistory = state.keywordHistory ?? (state.recentKeywords.length > 0 ? [state.recentKeywords] : [])
  const nextKeywordHistory = [...prevHistory, usedThisTurn].slice(-2)
  const nextRecentKeywords = Array.from(new Set(nextKeywordHistory.flat()))

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
      recentKeywords: nextRecentKeywords,
      keywordHistory: nextKeywordHistory,
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
    driftApplied = state.veilState === 'storm' ? -1.0 : -0.5
  }

  const { value, sealedOut } = applyGraceAndClamp(state.resonance + driftApplied, state)

  return {
    driftApplied: Number((value - state.resonance).toFixed(2)),
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

  const next = Math.max(0.0, Math.min(1000.0, Number((state.resonance + delta).toFixed(2))))
  const crossed450 = state.hasCrossedFirstThreshold || next >= 450.0

  return {
    appliedDelta: Number((next - state.resonance).toFixed(2)),
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
  if (state.resonance < 100.0) {
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
  const norm = resonance / 1000
  const dropProbability = Math.max(0.35, 1 - norm * 8)
  return line
    .split(/\s+/)
    .map((word, idx) => {
      const hash = ((word.charCodeAt(0) || 7) + idx * 13) % 100
      return hash / 100 < dropProbability ? '...' : word
    })
    .join(' ')
}
