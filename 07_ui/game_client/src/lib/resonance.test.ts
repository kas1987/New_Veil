import { describe, expect, it } from 'vitest'
import {
  applyDirectDelta,
  checkRoadAccess,
  createInitialSession,
  processNonTalkTurn,
  processTalkTurn,
  type ResonanceSessionState,
} from './resonanceSession'

describe('Resonance Psychometric & Session Engine', () => {
  it('starts at 0.350 and protects the grace floor for the first 5 talks below 0.450', () => {
    let state = createInitialSession()
    expect(state.resonance).toBe(0.35)

    for (let i = 0; i < 4; i++) {
      const res = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
      state = res.nextState
      expect(state.resonance).toBe(0.35)
      expect(res.evaluation.signals.graceFloorApplied).toBe(true)
    }

    const fifth = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
    state = fifth.nextState
    expect(state.resonance).toBe(0.35)

    const sixth = processTalkTurn(state, 'npc_guard', 'State your business.', 'ok')
    expect(sixth.nextState.resonance).toBe(0.32)
  })

  it('dissolves the grace floor immediately once the player crosses 0.450', () => {
    let state = createInitialSession()

    const turn1 = processTalkTurn(
      state,
      'npc_mira',
      'The lanterns flicker near the edge of the prism.',
      'Why do the lanterns flicker when I feel the prism pulling at my memory?',
    )
    state = turn1.nextState

    const turn2 = processTalkTurn(
      state,
      'npc_mira',
      'Because the town remembers who walked through before.',
      'I wonder what the town remembers about the shadow behind the veil?',
    )
    state = turn2.nextState
    expect(state.hasCrossedFirstThreshold).toBe(true)

    state = { ...state, resonance: 0.36 }
    const drop = processTalkTurn(state, 'npc_mira', 'Are you listening?', 'ok')
    expect(drop.nextState.resonance).toBe(0.34)
  })

  it('replaces positive gain with -0.030 friction on keyword dumps or commands', () => {
    const state = { ...createInitialSession(), turnsTaken: 6 }

    const dump = processTalkTurn(
      state,
      'npc_elder',
      'Speak plainly, traveler.',
      'veil quasar prism truth memory shadow dream trust',
    )
    expect(dump.evaluation.delta).toBe(-0.03)
    expect(dump.evaluation.signals.frictionType).toBe('command_or_dump_or_repeat')
  })

  it('awards +0.150 breakthrough surge on Hostile -> Bonded affective reversal, then reverts to +0.080 cap', () => {
    let state = { ...createInitialSession(), turnsTaken: 6, resonance: 0.4 }

    const t1 = processTalkTurn(
      state,
      'npc_warden',
      'Leave this wall before the fog takes your voice.',
      'I am afraid the fog will take my voice near this wall — why?',
      'hostile',
    )
    state = t1.nextState
    expect(t1.evaluation.cueType).toBe('saved_face_stabilized')
    expect(t1.evaluation.delta).toBe(0.08)

    const t2 = processTalkTurn(
      state,
      'npc_warden',
      'I watched three visitors vanish into that mist.',
      'I remember feeling that same mist in a dream, how did they vanish?',
      'hostile',
    )
    state = t2.nextState
    expect(t2.evaluation.updatedEncounter.currentStance).toBe('open')
    expect(t2.evaluation.delta).toBe(0.08)

    const t3 = processTalkTurn(
      state,
      'npc_warden',
      'You actually listened instead of demanding answers.',
      'I don’t know the truth of this place yet, so I trust your answers — how did you endure?',
      'hostile',
    )
    state = t3.nextState
    expect(t3.evaluation.cueType).toBe('breakthrough_surge')
    expect(t3.evaluation.delta).toBe(0.15)
    expect(state.resonance).toBe(0.71)

    const t4 = processTalkTurn(
      state,
      'npc_warden',
      'Stay close to the lantern line.',
      'I feel safer knowing the lantern line still holds against the shadow — how long has it burned?',
    )
    expect(t4.evaluation.delta).toBe(0.08)
  })

  it('applies high-band damping (+0.115 max breakthrough) at or above 0.800', () => {
    const state = {
      ...createInitialSession(),
      turnsTaken: 10,
      hasCrossedFirstThreshold: true,
      resonance: 0.81,
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
    expect(synthesis.evaluation.delta).toBe(0.115)
    expect(synthesis.nextState.resonance).toBe(0.925)
  })

  it('applies 3-turn Veil drift (-0.010 calm, -0.020 storm) and triggers < 0.100 Veil Suffocation', () => {
    let state: ResonanceSessionState = {
      ...createInitialSession(),
      turnsTaken: 8,
      hasCrossedFirstThreshold: true,
      resonance: 0.11,
      veilState: 'storm',
    }

    state = processNonTalkTurn(state).nextState
    state = processNonTalkTurn(state).nextState
    const third = processNonTalkTurn(state)
    state = third.nextState

    expect(third.driftApplied).toBe(-0.02)
    expect(state.resonance).toBe(0.09)

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
    expect(rescued.nextState.resonance).toBe(0.15)
    expect(checkRoadAccess(rescued.nextState, {}).allowed).toBe(true)
  })
})
