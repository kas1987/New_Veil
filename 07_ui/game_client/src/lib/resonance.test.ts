import { describe, expect, it } from 'vitest'
import corpus from '../../../../14_psychometrics/calibration_corpus.json'
import { evaluateTalkResonance, type TurnContext } from './resonanceEvaluator'
import {
  applyDirectDelta,
  checkRoadAccess,
  createInitialSession,
  processNonTalkTurn,
  processTalkTurn,
  type ResonanceSessionState,
} from './resonanceSession'

describe('Resonance Psychometric & Session Engine (3-Layer 0-1000 Scale)', () => {
  it('starts at 350.0 and protects the grace floor for the first 5 talks below 450.0', () => {
    let state = createInitialSession()
    expect(state.resonance).toBe(350.0)

    for (let i = 0; i < 4; i++) {
      const res = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
      state = res.nextState
      expect(state.resonance).toBe(350.0)
      expect(res.evaluation.signals.graceFloorApplied).toBe(true)
    }

    const fifth = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
    state = fifth.nextState
    expect(state.resonance).toBe(350.0)

    const sixth = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
    expect(sixth.nextState.resonance).toBe(348.8)
  })

  it('dissolves the grace floor immediately once the player crosses 450.0', () => {
    let state = { ...createInitialSession(), turnsTaken: 3, resonance: 448.5 }

    const pushOver = processTalkTurn(
      state,
      'npc_mira',
      'Because the town remembers who walked through before.',
      'I wonder what the town remembers about the shadow behind the veil?',
    )
    state = pushOver.nextState
    expect(state.resonance).toBeGreaterThanOrEqual(450.0)
    expect(state.hasCrossedFirstThreshold).toBe(true)

    state = { ...state, resonance: 360.0 }
    const drop = processTalkTurn(state, 'npc_mira', 'Are you listening?', 'ok')
    expect(drop.nextState.resonance).toBe(359.2)
  })

  it('replaces positive gain with -1.2 friction on keyword dumps or commands', () => {
    const state = { ...createInitialSession(), turnsTaken: 6 }

    const dump = processTalkTurn(
      state,
      'npc_elder',
      'Speak plainly, traveler.',
      'veil quasar prism truth memory shadow dream trust',
    )
    expect(dump.evaluation.delta).toBe(-1.2)
    expect(dump.evaluation.signals.frictionType).toBe('command_or_dump_or_repeat')
  })

  it('awards +6.0 breakthrough surge on Hostile -> Bonded affective reversal, then reverts to +2.5 cap', () => {
    let state = { ...createInitialSession(), turnsTaken: 6, resonance: 400.0 }

    const t1 = processTalkTurn(
      state,
      'npc_warden',
      'Leave this wall before the fog takes your voice.',
      'I am afraid the fog will take my voice near this wall — why?',
      'hostile',
    )
    state = t1.nextState
    expect(t1.evaluation.cueType).toBe('saved_face_stabilized')
    expect(t1.evaluation.delta).toBe(2.5)

    const t2 = processTalkTurn(
      state,
      'npc_warden',
      'I watched three visitors vanish into that mist.',
      'I remember feeling that same mist in a dream, how did they vanish?',
      'hostile',
    )
    state = t2.nextState
    expect(t2.evaluation.updatedEncounter.currentStance).toBe('open')
    expect(t2.evaluation.delta).toBe(2.5)

    const t3 = processTalkTurn(
      state,
      'npc_warden',
      'You actually listened instead of demanding answers.',
      'I don’t know the truth of this place yet, so I trust your answers — how did you endure?',
      'hostile',
    )
    state = t3.nextState
    expect(t3.evaluation.cueType).toBe('breakthrough_surge')
    expect(t3.evaluation.delta).toBe(6.0)
    expect(state.resonance).toBe(411.0)

    const t4 = processTalkTurn(
      state,
      'npc_warden',
      'Stay close to the lantern line.',
      'I feel safer knowing the lantern line still holds against the shadow — how long has it burned?',
    )
    expect(t4.evaluation.delta).toBe(2.5)
  })

  it('applies high-band damping (+4.0 max breakthrough) at or above 800.0', () => {
    const state = {
      ...createInitialSession(),
      turnsTaken: 10,
      hasCrossedFirstThreshold: true,
      resonance: 810.0,
    }

    const synthesis = processTalkTurn(
      state,
      'npc_mira',
      'The Dark Quasar only answers when the sky breaks.',
      'I remember reading about the quasar fracture, and I am afraid of what happens when the prism opens.',
      'open',
      ['quasar', 'fracture'],
    )

    expect(synthesis.evaluation.cueType).toBe('breakthrough_surge')
    expect(synthesis.evaluation.delta).toBe(4.0)
    expect(synthesis.nextState.resonance).toBe(814.0)
  })

  it('applies 3-turn Veil drift (-0.5 calm, -1.0 storm) and triggers < 100.0 Veil Suffocation', () => {
    let state: ResonanceSessionState = {
      ...createInitialSession(),
      turnsTaken: 8,
      hasCrossedFirstThreshold: true,
      resonance: 100.5,
      veilState: 'storm',
    }

    state = processNonTalkTurn(state).nextState
    state = processNonTalkTurn(state).nextState
    const third = processNonTalkTurn(state)
    state = third.nextState

    expect(third.driftApplied).toBe(-1.0)
    expect(state.resonance).toBe(99.5)

    const road = checkRoadAccess(state, {})
    expect(road.allowed).toBe(false)
    expect(road.reason).toBe('veil_suffocation_loop')
    expect(road.loopedToPlaza).toBe(true)

    const talk = processTalkTurn(
      state,
      'npc_mira',
      'Can you hear me?',
      'Please help me find the plaza lantern',
    )
    expect(talk.renderedPlayerText).toContain('...')

    const rescued = applyDirectDelta(state, { itemId: 'vial_of_memory_ash' })
    expect(rescued.nextState.resonance).toBe(109.5)
    expect(checkRoadAccess(rescued.nextState, {}).allowed).toBe(true)
  })

  it('penalizes long hostile dismissal, triggers Trust Rupture, amplifies 1.25x under Quasar, and cools stances', () => {
    // 1. Long mirrored line with hostility still fails as hostile_dismissal (-1.8)
    const hostileLong = processTalkTurn(
      { ...createInitialSession(), turnsTaken: 6, hasCrossedFirstThreshold: true, resonance: 500.0 },
      'npc_mira',
      'The lanterns burn gently along the plaza.',
      "I honestly don't care about your silly lanterns anymore.",
      'guarded',
    )
    expect(hostileLong.evaluation.delta).toBe(-1.8)
    expect(hostileLong.evaluation.signals.frictionType).toBe('hostile_dismissal')
    expect(hostileLong.evaluation.updatedEncounter.currentStance).toBe('hostile')

    // 2. Hostile dismissal on a bonded NPC triggers Trust Rupture (bonded -> guarded, -3.0)
    const bondedState: ResonanceSessionState = {
      ...createInitialSession(),
      turnsTaken: 8,
      hasCrossedFirstThreshold: true,
      resonance: 650.0,
      encounters: {
        npc_mira: {
          npcId: 'npc_mira',
          initialStance: 'guarded',
          currentStance: 'bonded',
          turnsSpentInResistance: 2,
          consecutiveAttunedTurns: 3,
          consecutiveFrictionTurns: 0,
          breakthroughAwarded: false,
          relevantUnlockedTokens: [],
          npcBond: 40.0,
          townContribution: 25.0,
        },
      },
    }
    const rupture = processTalkTurn(
      bondedState,
      'npc_mira',
      'I trusted you with this.',
      'Shut up, this is a waste of time.',
    )
    expect(rupture.evaluation.cueType).toBe('trust_rupture')
    expect(rupture.evaluation.signals.trustRupture).toBe(true)
    expect(rupture.evaluation.delta).toBe(-3.0)
    expect(rupture.evaluation.updatedEncounter.currentStance).toBe('guarded')

    // 3. Canon #15: Dark Quasar amplifies Trust Rupture by 1.25x (-3.0 -> -3.75)
    const quasarRupture = processTalkTurn(
      { ...bondedState, veilState: 'quasar_active' },
      'npc_mira',
      'The Quasar weighs on us.',
      'Shut up, you are lying.',
    )
    expect(quasarRupture.evaluation.signals.quasarAmplified).toBe(true)
    expect(quasarRupture.evaluation.delta).toBe(-3.75)

    // 4. Two consecutive standard friction turns cool open -> guarded
    let openState: ResonanceSessionState = {
      ...createInitialSession(),
      turnsTaken: 6,
      hasCrossedFirstThreshold: true,
      resonance: 500.0,
      encounters: {
        npc_mira: {
          npcId: 'npc_mira',
          initialStance: 'guarded',
          currentStance: 'open',
          turnsSpentInResistance: 1,
          consecutiveAttunedTurns: 2,
          consecutiveFrictionTurns: 0,
          breakthroughAwarded: false,
          relevantUnlockedTokens: [],
          npcBond: 20.0,
          townContribution: 12.0,
        },
      },
    }
    openState = processTalkTurn(openState, 'npc_mira', 'Are you still there?', 'ok').nextState
    expect(openState.encounters.npc_mira.currentStance).toBe('open')
    openState = processTalkTurn(openState, 'npc_mira', 'Say something real.', 'yeah').nextState
    expect(openState.encounters.npc_mira.currentStance).toBe('guarded')
  })

  it('soft-tapers global Town Resonance after +50 per NPC while growing personal Bond to 100 in ~25 turns', () => {
    let state = { ...createInitialSession(), turnsTaken: 6, hasCrossedFirstThreshold: true, resonance: 350.0 }
    const themes = ['why', 'memory', 'dream', 'truth']
    for (let i = 0; i < 25; i++) {
      const npcReply = 'The lanterns near the Listening Wall go out whenever the fog remembers who built them.'
      const turn = processTalkTurn(
        state,
        'mira',
        npcReply,
        `I feel uncertain about wall ${i} and ${themes[i % themes.length]} — how do the lanterns remember?`,
      )
      state = turn.nextState
    }
    const miraEnc = state.encounters.mira
    expect(miraEnc.npcBond).toBe(100.0)
    expect(state.resonance).toBeLessThan(410.0)
  })

  it('advances the rolling 2-turn keyword-fatigue window across sandbox turns', () => {
    let state = { ...createInitialSession(), turnsTaken: 6, hasCrossedFirstThreshold: true, resonance: 500.0 }

    const t1 = processTalkTurn(
      state,
      'mira',
      'The lanterns burn softly tonight.',
      'I wonder why the lanterns stay bright near the veil tonight?',
    )
    expect(t1.evaluation.signals.resonantWordsHit).toContain('veil')
    expect(t1.nextState.recentKeywords).toContain('veil')
    state = t1.nextState

    // Next turn repeating 'veil' triggers keyword fatigue instead of fresh bonus
    const t2 = processTalkTurn(
      state,
      'mira',
      'Some visitors ask too quickly.',
      'I feel uncertain when the veil hides behind warm lanterns?',
    )
    expect(t2.evaluation.signals.fatiguedWords).toContain('veil')
    expect(t2.evaluation.signals.resonantWordsHit).not.toContain('veil')
    state = t2.nextState

    // Two turns without thematic words clear 'veil' from recentKeywords
    state = processTalkTurn(state, 'mira', 'Walk calmly.', 'I hear the wind in the trees tonight.').nextState
    state = processTalkTurn(state, 'mira', 'Keep listening.', 'I feel quieter watching the warm glass tonight.').nextState
    expect(state.recentKeywords).not.toContain('veil')
  })

  it.each(corpus.single_turn_probes)(
    'matches shared calibration_corpus.json probe: $id',
    (probe) => {
      const ctx: TurnContext = {
        currentResonance: probe.ctx.currentResonance,
        turnsTaken: probe.ctx.turnsTaken,
        hasCrossedFirstThreshold: probe.ctx.hasCrossedFirstThreshold,
        npcLastLine: probe.ctx.npcLastLine,
        recentKeywords: probe.ctx.recentKeywords ?? [],
        veilState: probe.ctx.veilState as TurnContext['veilState'],
        playerLastLine: (probe.ctx as { playerLastLine?: string }).playerLastLine ?? '',
        encounter: (probe.ctx as { encounter?: TurnContext['encounter'] }).encounter,
        personalityWeights: (probe.ctx as { personalityWeights?: TurnContext['personalityWeights'] })
          .personalityWeights,
      }
      const res = evaluateTalkResonance(probe.playerLine, ctx)
      const exp = probe.expected as Record<string, unknown>

      if ('delta' in exp) expect(res.delta).toBe(exp.delta)
      if ('newResonance' in exp) expect(res.newResonance).toBe(exp.newResonance)
      if ('cueType' in exp) expect(res.cueType).toBe(exp.cueType)
      if ('stance' in exp) expect(res.updatedEncounter.currentStance).toBe(exp.stance)
      if ('frictionType' in exp) expect(res.signals.frictionType).toBe(exp.frictionType)
      if ('mirroredNpc' in exp) expect(res.signals.mirroredNpc).toBe(exp.mirroredNpc)
      if ('openInquiry' in exp) expect(res.signals.openInquiry).toBe(exp.openInquiry)
      if ('interiority' in exp) expect(res.signals.interiority).toBe(exp.interiority)
      if ('thematicInSentence' in exp) expect(res.signals.thematicInSentence).toBe(exp.thematicInSentence)
      if ('sustainedCadence' in exp) expect(res.signals.sustainedCadence).toBe(exp.sustainedCadence)
      if ('resonantWordsHit' in exp) expect(res.signals.resonantWordsHit).toEqual(exp.resonantWordsHit)
      if ('graceFloorApplied' in exp) expect(res.signals.graceFloorApplied).toBe(exp.graceFloorApplied)
      if ('hitSaturationCap' in exp) expect(res.signals.hitSaturationCap).toBe(exp.hitSaturationCap)
      if ('trustRupture' in exp) expect(res.signals.trustRupture).toBe(exp.trustRupture)
      if ('quasarAmplified' in exp) expect(res.signals.quasarAmplified).toBe(exp.quasarAmplified)
      if ('integrativeSynthesis' in exp) expect(res.signals.integrativeSynthesis).toBe(exp.integrativeSynthesis)
      if ('npcTaperApplied' in exp) expect(res.signals.npcTaperApplied).toBe(exp.npcTaperApplied)
      if ('npcBond' in exp) expect(res.signals.npcBond).toBe(exp.npcBond)
    },
  )
})
