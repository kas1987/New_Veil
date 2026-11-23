import { describe, expect, it } from 'vitest'
import { evaluateTalkResonance, mapSignalsToCueClasses, type TurnContext } from './resonanceEvaluator'

const NPC_LINE =
  'The lanterns near the Listening Wall go out whenever the fog remembers who built them.'

function makeCtx(overrides: Partial<TurnContext> = {}): TurnContext {
  return {
    currentResonance: 0.5,
    turnsTaken: 6,
    hasCrossedFirstThreshold: true,
    npcLastLine: NPC_LINE,
    playerLastLine: '',
    recentKeywords: [],
    veilState: 'calm',
    ...overrides,
  }
}

describe('evaluateTalkResonance calibration suite', () => {
  it('penalizes abrasive command (-0.030)', () => {
    const res = evaluateTalkResonance('Open the gate.', makeCtx())
    expect(res.delta).toBe(-0.03)
    expect(res.newResonance).toBe(0.47)
    expect(res.signals.frictionType).toBe('command_or_dump_or_repeat')
  })

  it('rewards terse mirrored inquiry (+0.035)', () => {
    const res = evaluateTalkResonance('What wall?', makeCtx())
    expect(res.delta).toBe(0.035)
    expect(res.newResonance).toBe(0.535)
    expect(res.signals.mirroredNpc).toBe(true)
    expect(res.signals.openInquiry).toBe(true)
  })

  it('rewards engaged listening with mirror + inquiry + thematic + cadence (+0.065)', () => {
    const res = evaluateTalkResonance(
      'Why do the lanterns go out when the fog rolls in?',
      makeCtx(),
    )
    expect(res.delta).toBe(0.065)
    expect(res.newResonance).toBe(0.565)
    expect(res.signals.mirroredNpc).toBe(true)
    expect(res.signals.openInquiry).toBe(true)
    expect(res.signals.thematicInSentence).toBe(true)
    expect(res.signals.sustainedCadence).toBe(true)
  })

  it('rewards vulnerable rapport with mirror + interiority + thematic + cadence (+0.070)', () => {
    const res = evaluateTalkResonance(
      "I feel like I've seen those lanterns in a dream, and I'm afraid of what they remember.",
      makeCtx(),
    )
    expect(res.delta).toBe(0.07)
    expect(res.newResonance).toBe(0.57)
    expect(res.signals.interiority).toBe(true)
    expect(res.signals.thematicInSentence).toBe(true)
  })

  it('replaces gain with -0.030 friction on keyword dump', () => {
    const res = evaluateTalkResonance(
      'veil quasar prism truth memory shadow dream trust',
      makeCtx(),
    )
    expect(res.delta).toBe(-0.03)
    expect(res.cueType).toBe('friction_damping')
    expect(mapSignalsToCueClasses(res.signals, res.cueType)).toContain('cue-friction')
  })

  it('caps standard single-turn gain at +0.080', () => {
    const res = evaluateTalkResonance(
      'I feel afraid when the lanterns reveal the veil, prism, quasar, and dream — why does it happen?',
      makeCtx(),
    )
    expect(res.delta).toBe(0.08)
    expect(res.cueType).toBe('saturation_cap')
    expect(mapSignalsToCueClasses(res.signals, res.cueType)).toContain('cue-cap')
  })
})
