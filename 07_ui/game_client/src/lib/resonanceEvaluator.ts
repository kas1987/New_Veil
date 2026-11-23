export type EncounterStance = 'hostile' | 'guarded' | 'open' | 'bonded'

export type CueType =
  | 'collapse_static'
  | 'trust_rupture'
  | 'friction_damping'
  | 'saved_face_stabilized'
  | 'standard_harmonic'
  | 'saturation_cap'
  | 'breakthrough_surge'

export interface PersonalityWeights {
  mirror?: number
  inquiry?: number
  interiority?: number
  thematic?: number
  cadence?: number
}

export interface NpcEncounterState {
  npcId: string
  initialStance: EncounterStance
  currentStance: EncounterStance
  turnsSpentInResistance: number
  consecutiveAttunedTurns: number
  consecutiveFrictionTurns?: number
  breakthroughAwarded: boolean
  relevantUnlockedTokens: string[]
  npcBond?: number
  townContribution?: number
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
  personalityWeights?: PersonalityWeights
}

export interface ResonanceSignals {
  mirroredNpc: boolean
  openInquiry: boolean
  interiority: boolean
  thematicInSentence: boolean
  sustainedCadence: boolean
  frictionType: 'none' | 'terse_filler' | 'command_or_dump_or_repeat' | 'hostile_dismissal'
  integrativeSynthesis: boolean
  stanceTransition: string | null
  graceFloorApplied: boolean
  trustRupture?: boolean
  quasarAmplified?: boolean
  npcTaperApplied?: boolean
  npcBond?: number
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

export const TOWN_MAX = 1000.0
export const GRACE_FLOOR = 350.0
export const COLLAPSE_THRESHOLD = 100.0
export const QUASAR_RESONANCE_THRESHOLD = 600.0
export const TURN_CAP = 2.5
export const ATTUNED_MIN_DELTA = 1.1
export const BREAKTHROUGH_BONUS = 3.5
export const BREAKTHROUGH_CEILING = 6.0
export const HIGH_BAND_FROM = 800.0
export const HIGH_BAND_CEILING = 4.0
export const NPC_CONTRIBUTION_SOFT_CAP = 50.0
export const NPC_TAPER_MULTIPLIER = 0.15
export const NPC_BOND_GAIN_MULTIPLIER = 1.6
export const NPC_BOND_LOSS_MULTIPLIER = 1.5
export const NPC_BREAKTHROUGH_BOND_BONUS = 10.0

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

const HOSTILE_DISMISSAL_RE =
  /\b(shut up|stop talking|don't care|don’t care|do not care|waste of time|pathetic|useless|boring|stupid|annoying|liar|you're lying|you’re lying|you are lying|leave me alone|get lost|whatever you say|fake town)\b/i

const COMMAND_OR_FILLER =
  /^(ok|okay|yes|no|yeah|nah|sure|fine|whatever|huh|what|give|open|unlock|tell me|show me|go|leave|bye)\b[.!?]*$/i

function round2(value: number): number {
  if (Math.abs(value) < 1e-12) return 0
  const sign = value < 0 ? -1 : 1
  return (sign * Math.floor(Math.abs(value) * 100 + 0.5 + 1e-9)) / 100
}

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
    ? {
        ...ctx.encounter,
        relevantUnlockedTokens: [...ctx.encounter.relevantUnlockedTokens],
        npcBond: ctx.encounter.npcBond ?? 0.0,
        townContribution: ctx.encounter.townContribution ?? 0.0,
      }
    : {
        npcId: 'default',
        initialStance: 'guarded',
        currentStance: 'guarded',
        turnsSpentInResistance: 0,
        consecutiveAttunedTurns: 0,
        breakthroughAwarded: false,
        relevantUnlockedTokens: [],
        npcBond: 0.0,
        townContribution: 0.0,
      }
  let stanceTransition: string | null = null

  const weights = ctx.personalityWeights ?? {}
  const wMirror = weights.mirror ?? 1.0
  const wInquiry = weights.inquiry ?? 1.0
  const wInteriority = weights.interiority ?? 1.0
  const wThematic = weights.thematic ?? 1.0
  const wCadence = weights.cadence ?? 1.0

  const prevPlayerLine = (ctx.playerLastLine ?? '').trim().toLowerCase()
  const isHostileDismissal = HOSTILE_DISMISSAL_RE.test(trimmed)
  const isRepeatLine = trimmed.length > 0 && prevPlayerLine.length > 0 && lower === prevPlayerLine
  const isCommand = /^(give|open|unlock|go|leave|show me|tell me the)\b/i.test(trimmed)
  const isDump = isKeywordDump(tokens, trimmed)
  const isTerseOrFiller = trimmed.length < 15 || COMMAND_OR_FILLER.test(trimmed)

  let frictionType: ResonanceSignals['frictionType'] = 'none'
  let rawDelta = 0

  if (isHostileDismissal) {
    frictionType = 'hostile_dismissal'
    rawDelta = -1.8
  } else if (isRepeatLine || isCommand || isDump) {
    frictionType = 'command_or_dump_or_repeat'
    rawDelta = -1.2
  } else if (isTerseOrFiller && !tokens.some((t) => npcTokens.has(t))) {
    frictionType = 'terse_filler'
    rawDelta = -0.8
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
    if (mirroredNpc) rawDelta += round2(0.6 * wMirror)

    openInquiry =
      trimmed.includes('?') ||
      /^(how|why|what do you|tell me about|i wonder)\b/i.test(trimmed)
    if (openInquiry) rawDelta += round2(0.5 * wInquiry)

    interiority = INTERIORITY_PATTERNS.some((rx) => rx.test(trimmed))
    for (const w of Array.from(new Set(tokens))) {
      if (THEMATIC_WORDS.has(w)) {
        if (ctx.recentKeywords.includes(w)) fatiguedWords.push(w)
        else resonantWordsHit.push(w)
      }
    }
    thematicInSentence = resonantWordsHit.length > 0 && trimmed.split(/\s+/).length >= 4

    let depthBonus = 0
    if (interiority) depthBonus += 0.6 * wInteriority
    if (thematicInSentence) depthBonus += 0.6 * wThematic
    rawDelta += round2(Math.min(1.2, depthBonus))

    sustainedCadence = trimmed.length > 45
    if (sustainedCadence) rawDelta += round2(0.3 * wCadence)
    rawDelta = round2(rawDelta)
  }

  let breakthroughTriggered = false
  let integrativeSynthesis = false
  let trustRupture = false
  let quasarAmplified = false
  const prevStance = encounter.currentStance

  if (frictionType !== 'none') {
    encounter.consecutiveAttunedTurns = 0
    const consecFriction = (encounter.consecutiveFrictionTurns ?? 0) + 1
    encounter.consecutiveFrictionTurns = consecFriction

    if (frictionType === 'hostile_dismissal') {
      if (prevStance === 'bonded') {
        encounter.currentStance = 'guarded'
        stanceTransition = 'bonded -> guarded'
        trustRupture = true
        rawDelta = -3.0
      } else if (prevStance === 'open') {
        encounter.currentStance = 'hostile'
        stanceTransition = 'open -> hostile'
        trustRupture = true
        rawDelta = -3.0
      } else if (prevStance === 'guarded') {
        encounter.currentStance = 'hostile'
        stanceTransition = 'guarded -> hostile'
      }
    } else {
      if (prevStance === 'guarded') {
        encounter.currentStance = 'hostile'
        stanceTransition = 'guarded -> hostile'
      } else if (prevStance === 'open' && consecFriction >= 2) {
        encounter.currentStance = 'guarded'
        stanceTransition = 'open -> guarded'
      } else if (prevStance === 'bonded' && consecFriction >= 2) {
        encounter.currentStance = 'open'
        stanceTransition = 'bonded -> open'
      }
    }

    // Canon #15: Dark Quasar amplifies negative signals by 25% on high-trust/high-resonance bonds
    if (
      ctx.veilState === 'quasar_active' &&
      (ctx.currentResonance >= QUASAR_RESONANCE_THRESHOLD || prevStance === 'open' || prevStance === 'bonded')
    ) {
      rawDelta = round2(rawDelta * 1.25)
      quasarAmplified = true
    }
  } else if (rawDelta >= ATTUNED_MIN_DELTA) {
    encounter.consecutiveFrictionTurns = 0
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
      rawDelta = round2(rawDelta + BREAKTHROUGH_BONUS)
    }
  }

  let hitSaturationCap = false
  if (rawDelta > 0) {
    let cap = TURN_CAP
    if (breakthroughTriggered) {
      cap = ctx.currentResonance >= HIGH_BAND_FROM ? HIGH_BAND_CEILING : BREAKTHROUGH_CEILING
    }
    if (rawDelta >= cap) {
      rawDelta = cap
      hitSaturationCap = true
    }
  }

  // Personal NPC Bond updates from pre-taper rawDelta
  const prevBond = encounter.npcBond ?? 0.0
  let bondDelta = 0.0
  if (breakthroughTriggered) {
    bondDelta = NPC_BREAKTHROUGH_BOND_BONUS
  } else if (rawDelta > 0) {
    bondDelta = round2(rawDelta * NPC_BOND_GAIN_MULTIPLIER)
  } else if (rawDelta < 0) {
    bondDelta = round2(rawDelta * NPC_BOND_LOSS_MULTIPLIER)
  }
  const nextBond = Math.max(0.0, Math.min(100.0, round2(prevBond + bondDelta)))
  encounter.npcBond = nextBond

  // Soft taper per NPC after +50.0 global Town Resonance contribution (positive gains only)
  const prevContrib = encounter.townContribution ?? 0.0
  let npcTaperApplied = false
  let townDelta = rawDelta
  if (rawDelta > 0) {
    if (prevContrib >= NPC_CONTRIBUTION_SOFT_CAP) {
      townDelta = round2(rawDelta * NPC_TAPER_MULTIPLIER)
      npcTaperApplied = true
    } else if (prevContrib + rawDelta > NPC_CONTRIBUTION_SOFT_CAP) {
      const fullPart = NPC_CONTRIBUTION_SOFT_CAP - prevContrib
      const remPart = rawDelta - fullPart
      townDelta = round2(fullPart + remPart * NPC_TAPER_MULTIPLIER)
      npcTaperApplied = true
    }
    encounter.townContribution = round2(prevContrib + townDelta)
  }

  const inGraceWindow = ctx.turnsTaken < 5 && !ctx.hasCrossedFirstThreshold
  let nextValue = round2(ctx.currentResonance + townDelta)
  let graceFloorApplied = false

  if (inGraceWindow && nextValue < GRACE_FLOOR) {
    nextValue = GRACE_FLOOR
    graceFloorApplied = true
  }

  nextValue = Math.max(0.0, Math.min(TOWN_MAX, nextValue))
  const finalDelta = round2(nextValue - ctx.currentResonance)

  let cueType: CueType = 'standard_harmonic'
  if (nextValue < COLLAPSE_THRESHOLD) {
    cue_type_collapse: {
      cueType = 'collapse_static'
      break cue_type_collapse
    }
  } else if (trustRupture) {
    cueType = 'trust_rupture'
  } else if (frictionType !== 'none') {
    cueType = 'friction_damping'
  } else if (breakthroughTriggered) {
    cueType = 'breakthrough_surge'
  } else if (stanceTransition === 'hostile -> guarded') {
    cueType = 'saved_face_stabilized'
  } else if (hitSaturationCap && !npcTaperApplied) {
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
      trustRupture,
      quasarAmplified,
      npcTaperApplied,
      npcBond: nextBond,
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
  if (cueType === 'trust_rupture' || signals?.trustRupture) classes.push('cue-rupture')
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
