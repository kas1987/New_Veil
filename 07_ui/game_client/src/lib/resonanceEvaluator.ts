export type EncounterStance = 'hostile' | 'guarded' | 'open' | 'bonded'

export type CueType =
  | 'collapse_static'
  | 'friction_damping'
  | 'saved_face_stabilized'
  | 'standard_harmonic'
  | 'saturation_cap'
  | 'breakthrough_surge'

export interface NpcEncounterState {
  npcId: string
  initialStance: EncounterStance
  currentStance: EncounterStance
  turnsSpentInResistance: number
  consecutiveAttunedTurns: number
  breakthroughAwarded: boolean
  relevantUnlockedTokens: string[]
}

export interface TurnContext {
  currentResonance: number
  turnsTaken: number
  hasCrossedFirstThreshold: boolean
  npcLastLine: string
  playerLastLine?: string
  recentKeywords: string[]
  veilState: 'calm' | 'still' | 'storm' | 'quasar_active'
  encounter?: NpcEncounterState
}

export interface ResonanceSignals {
  mirroredNpc: boolean
  openInquiry: boolean
  interiority: boolean
  thematicInSentence: boolean
  sustainedCadence: boolean
  frictionType: 'none' | 'terse_filler' | 'command_or_dump_or_repeat'
  integrativeSynthesis: boolean
  stanceTransition: string | null
  graceFloorApplied: boolean
  vulnerableFraming?: boolean
  resonantWordsHit?: string[]
  fatiguedWords?: string[]
  isDismissiveOrTransactional?: boolean
  hitSaturationCap?: boolean
}

export interface ResonanceEvaluation {
  newResonance: number
  delta: number
  updatedEncounter: NpcEncounterState
  cueType: CueType
  signals: ResonanceSignals
}

export const THEMATIC_WORDS = new Set([
  'veil',
  'quasar',
  'prism',
  'truth',
  'memory',
  'shadow',
  'dream',
  'trust',
  'fear',
  'why',
])

const STOPWORDS = new Set([
  'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'any', 'can',
  'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him',
  'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
  'that', 'this', 'with', 'have', 'from', 'they', 'will', 'what', 'when',
  'your', 'there', 'their', 'about', 'would', 'could', 'should', 'here',
])

const INTERIORITY_PATTERNS = [
  /\bi\s+(feel|felt|remember|wonder|fear|doubt|hope|wish|miss|believe|don't know|don’t know|do not know|can't|can’t|cannot)\b/i,
  /\b(i'm afraid|i’m afraid|i am afraid|uncertain|lost|alone|tired|honestly|truthfully)\b/i,
]

const COMMAND_OR_FILLER =
  /^(ok|okay|yes|no|yeah|nah|sure|fine|whatever|huh|what|give|open|unlock|tell me|show me|go|leave|bye)\b[.!?]*$/i

export function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9'’\s]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 2 && !STOPWORDS.has(w))
}

function isKeywordDump(tokens: string[], rawText: string): boolean {
  if (tokens.length < 2) return false
  const thematicCount = tokens.filter((t) => THEMATIC_WORDS.has(t)).length
  const wordCount = rawText.trim().split(/\s+/).length
  return thematicCount >= 2 && thematicCount / wordCount >= 0.6
}

export function evaluateTalkResonance(
  playerLine: string,
  ctx: TurnContext,
): ResonanceEvaluation {
  const trimmed = playerLine.trim()
  const lower = trimmed.toLowerCase()
  const tokens = tokenize(trimmed)
  const npcTokens = new Set(tokenize(ctx.npcLastLine))

  const encounter: NpcEncounterState = ctx.encounter
    ? { ...ctx.encounter, relevantUnlockedTokens: [...ctx.encounter.relevantUnlockedTokens] }
    : {
        npcId: 'default',
        initialStance: 'guarded',
        currentStance: 'guarded',
        turnsSpentInResistance: 0,
        consecutiveAttunedTurns: 0,
        breakthroughAwarded: false,
        relevantUnlockedTokens: [],
      }
  let stanceTransition: string | null = null

  const prevPlayerLine = (ctx.playerLastLine ?? '').trim().toLowerCase()
  const isRepeatLine = trimmed.length > 0 && prevPlayerLine.length > 0 && lower === prevPlayerLine
  const isCommand = /^(give|open|unlock|go|leave|show me|tell me the)\b/i.test(trimmed)
  const isDump = isKeywordDump(tokens, trimmed)
  const isTerseOrFiller = trimmed.length < 15 || COMMAND_OR_FILLER.test(trimmed)

  let frictionType: ResonanceSignals['frictionType'] = 'none'
  let rawDelta = 0

  if (isRepeatLine || isCommand || isDump) {
    frictionType = 'command_or_dump_or_repeat'
    rawDelta = -0.03
  } else if (isTerseOrFiller && !tokens.some((t) => npcTokens.has(t))) {
    frictionType = 'terse_filler'
    rawDelta = -0.02
  }

  let mirroredNpc = false
  let openInquiry = false
  let interiority = false
  let thematicInSentence = false
  let sustainedCadence = false
  const resonantWordsHit: string[] = []
  const fatiguedWords: string[] = []

  if (frictionType === 'none') {
    mirroredNpc = tokens.some((t) => npcTokens.has(t))
    if (mirroredNpc) rawDelta += 0.02

    openInquiry =
      trimmed.includes('?') ||
      /^(how|why|what do you|tell me about|i wonder)\b/i.test(trimmed)
    if (openInquiry) rawDelta += 0.015

    interiority = INTERIORITY_PATTERNS.some((rx) => rx.test(trimmed))
    for (const w of Array.from(new Set(tokens))) {
      if (THEMATIC_WORDS.has(w)) {
        if (ctx.recentKeywords.includes(w)) fatiguedWords.push(w)
        else resonantWordsHit.push(w)
      }
    }
    thematicInSentence = resonantWordsHit.length > 0 && trimmed.split(/\s+/).length >= 4

    let depthBonus = 0
    if (interiority) depthBonus += 0.02
    if (thematicInSentence) depthBonus += 0.02
    rawDelta += Math.min(0.04, depthBonus)

    sustainedCadence = trimmed.length > 45
    if (sustainedCadence) rawDelta += 0.01
  }

  let breakthroughTriggered = false
  let integrativeSynthesis = false

  if (frictionType !== 'none') {
    encounter.consecutiveAttunedTurns = 0
    if (encounter.currentStance === 'guarded') {
      encounter.currentStance = 'hostile'
      stanceTransition = 'guarded -> hostile'
    }
  } else if (rawDelta >= 0.035) {
    encounter.consecutiveAttunedTurns += 1

    if (encounter.currentStance === 'hostile' || encounter.currentStance === 'guarded') {
      encounter.turnsSpentInResistance += 1
    }

    if (encounter.currentStance === 'hostile' && encounter.consecutiveAttunedTurns >= 1) {
      encounter.currentStance = 'guarded'
      stanceTransition = 'hostile -> guarded'
    } else if (encounter.currentStance === 'guarded' && encounter.consecutiveAttunedTurns >= 2) {
      encounter.currentStance = 'open'
      stanceTransition = 'guarded -> open'
    } else if (encounter.currentStance === 'open' && encounter.consecutiveAttunedTurns >= 3) {
      encounter.currentStance = 'bonded'
      stanceTransition = 'open -> bonded'
    }

    const referencedLore = tokens.some((t) => encounter.relevantUnlockedTokens.includes(t))
    if (interiority && referencedLore) {
      integrativeSynthesis = true
    }

    const affectiveReversal =
      encounter.initialStance === 'hostile' &&
      encounter.turnsSpentInResistance >= 2 &&
      encounter.currentStance === 'bonded'

    if (!encounter.breakthroughAwarded && (affectiveReversal || integrativeSynthesis)) {
      breakthroughTriggered = true
      encounter.breakthroughAwarded = true
      rawDelta += 0.07
    }
  }

  let hitSaturationCap = false
  if (rawDelta > 0) {
    let cap = 0.08
    if (breakthroughTriggered) {
      cap = ctx.currentResonance >= 0.8 ? 0.115 : 0.15
    }
    if (rawDelta >= cap) {
      rawDelta = cap
      hitSaturationCap = true
    }
  }

  const inGraceWindow = ctx.turnsTaken < 5 && !ctx.hasCrossedFirstThreshold
  let nextValue = Number((ctx.currentResonance + rawDelta).toFixed(3))
  let graceFloorApplied = false

  if (inGraceWindow && nextValue < 0.35) {
    nextValue = 0.35
    graceFloorApplied = true
  }

  nextValue = Math.max(0.0, Math.min(1.0, nextValue))
  const finalDelta = Number((nextValue - ctx.currentResonance).toFixed(3))

  let cueType: CueType = 'standard_harmonic'
  if (nextValue < 0.1) {
    cueType = 'collapse_static'
  } else if (frictionType !== 'none') {
    cueType = 'friction_damping'
  } else if (breakthroughTriggered) {
    cueType = 'breakthrough_surge'
  } else if (stanceTransition === 'hostile -> guarded') {
    cueType = 'saved_face_stabilized'
  } else if (finalDelta >= 0.08) {
    cueType = 'saturation_cap'
  }

  return {
    newResonance: nextValue,
    delta: finalDelta,
    updatedEncounter: encounter,
    cueType,
    signals: {
      mirroredNpc,
      openInquiry,
      interiority,
      thematicInSentence,
      sustainedCadence,
      frictionType,
      integrativeSynthesis,
      stanceTransition,
      graceFloorApplied,
      vulnerableFraming: interiority,
      resonantWordsHit,
      fatiguedWords,
      isDismissiveOrTransactional: frictionType !== 'none',
      hitSaturationCap,
    },
  }
}

export function mapSignalsToCueClasses(
  signals?: ResonanceSignals | null,
  cueType?: CueType | null,
): string {
  const classes: string[] = []
  if (cueType === 'breakthrough_surge') classes.push('cue-breakthrough')
  if (cueType === 'saved_face_stabilized') classes.push('cue-stabilized')
  if (cueType === 'collapse_static') classes.push('cue-collapse')
  if (signals?.hitSaturationCap || cueType === 'saturation_cap') classes.push('cue-cap')
  if (signals?.interiority || signals?.vulnerableFraming) classes.push('cue-vulnerable')
  if (signals?.mirroredNpc) classes.push('cue-mirror')
  if (
    cueType === 'friction_damping' ||
    (signals?.frictionType && signals.frictionType !== 'none') ||
    (signals?.fatiguedWords && signals.fatiguedWords.length > 0)
  ) {
    classes.push('cue-friction')
  }
  return Array.from(new Set(classes)).join(' ')
}
