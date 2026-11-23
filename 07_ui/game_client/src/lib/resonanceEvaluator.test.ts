import { describe, expect, it } from 'vitest'
import { evaluateTalkResonance, mapSignalsToCueClasses, type TurnContext } from './resonanceEvaluator'

const NPC_LINE =
  'The lanterns near the Listening Wall go out whenever the fog remembers who built them.'

function makeCtx(overrides: Partial<TurnContext> = {}): TurnContext {
  return {
    currentResonance: 500.0,
    turnsTaken: 6,
    hasCrossedFirstThreshold: true,
    npcLastLine: NPC_LINE,
    playerLastLine: '',
    recentKeywords: [],
    veilState: 'calm',
    ...overrides,
  }
}

describe('evaluateTalkResonance calibration suite (0-1000 Scale)', () => {
  it('penalizes abrasive command (-1.2)', () => {
    const res = evaluateTalkResonance('Open the gate.', makeCtx())
    expect(res.delta).toBe(-1.2)
    expect(res.newResonance).toBe(498.8)
    expect(res.signals.frictionType).toBe('command_or_dump_or_repeat')
  })

  it('rewards terse mirrored inquiry (+1.1)', () => {
    const res = evaluateTalkResonance('What wall?', makeCtx())
    expect(res.delta).toBe(1.1)
    expect(res.newResonance).toBe(501.1)
    expect(res.signals.mirroredNpc).toBe(true)
    expect(res.signals.openInquiry).toBe(true)
  })

  it('rewards engaged listening with mirror + inquiry + thematic + cadence (+2.0)', () => {
    const res = evaluateTalkResonance(
      'Why do the lanterns go out when the fog rolls in?',
      makeCtx(),
    )
    expect(res.delta).toBe(2.0)
    expect(res.newResonance).toBe(502.0)
    expect(res.signals.mirroredNpc).toBe(true)
    expect(res.signals.openInquiry).toBe(true)
    expect(res.signals.thematicInSentence).toBe(true)
    expect(res.signals.sustainedCadence).toBe(true)
  })

  it('rewards vulnerable rapport with mirror + interiority + thematic + cadence (+2.1)', () => {
    const res = evaluateTalkResonance(
      "I feel like I've seen those lanterns in a dream, and I'm afraid of what they remember.",
      makeCtx(),
    )
    expect(res.delta).toBe(2.1)
    expect(res.newResonance).toBe(502.1)
    expect(res.signals.interiority).toBe(true)
    expect(res.signals.thematicInSentence).toBe(true)
  })

  it('replaces gain with -1.2 friction on keyword dump', () => {
    const res = evaluateTalkResonance(
      'veil quasar prism truth memory shadow dream trust',
      makeCtx(),
    )
    expect(res.delta).toBe(-1.2)
    expect(res.cueType).toBe('friction_damping')
    expect(mapSignalsToCueClasses(res.signals, res.cueType)).toContain('cue-friction')
  })

  it('caps standard single-turn gain at +2.5', () => {
    const res = evaluateTalkResonance(
      'I feel afraid when the lanterns reveal the veil, prism, quasar, and dream — why does it happen?',
      makeCtx(),
    )
    expect(res.delta).toBe(2.5)
    expect(res.cueType).toBe('saturation_cap')
    expect(mapSignalsToCueClasses(res.signals, res.cueType)).toContain('cue-cap')
  })
})
