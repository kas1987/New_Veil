import { afterEach, describe, expect, it, vi } from 'vitest'
import { VeilAudioEngine } from './veilAudio'

describe('VeilAudioEngine procedural harmonic cues', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('is a safe no-op when muted or when Web Audio is unavailable', () => {
    const audio = new VeilAudioEngine()
    expect(audio.isEnabled()).toBe(false)
    expect(() => audio.playDialogueCue('breakthrough_surge', null, 6.0)).not.toThrow()
    expect(() => audio.playInspectCue(true)).not.toThrow()
    expect(() => audio.playVeilShiftCue('quasar_active')).not.toThrow()

    // Even when enabled in an environment without AudioContext (jsdom), no error throws
    audio.setEnabled(true)
    expect(() => audio.playDialogueCue('trust_rupture', null, -3.0)).not.toThrow()
  })

  it('synthesizes oscillators when enabled with a working AudioContext', () => {
    const createdOscillators: Array<{ type: OscillatorType; freq: number }> = []

    class MockAudioContext {
      state = 'running'
      currentTime = 0
      destination = {}
      resume = vi.fn().mockResolvedValue(undefined)
      createOscillator() {
        const osc = {
          type: 'sine' as OscillatorType,
          frequency: {
            setValueAtTime: vi.fn((freq: number) => {
              createdOscillators.push({ type: osc.type, freq })
            }),
            exponentialRampToValueAtTime: vi.fn(),
          },
          connect: vi.fn(),
          start: vi.fn(),
          stop: vi.fn(),
        }
        return osc
      }
      createGain() {
        return {
          gain: {
            setValueAtTime: vi.fn(),
            linearRampToValueAtTime: vi.fn(),
            exponentialRampToValueAtTime: vi.fn(),
          },
          connect: vi.fn(),
        }
      }
    }

    vi.stubGlobal('AudioContext', MockAudioContext)
    const audio = new VeilAudioEngine()
    audio.playDialogueCue('breakthrough_surge', null, 6.0)
    expect(createdOscillators).toHaveLength(0)

    audio.setEnabled(true)
    audio.playDialogueCue('breakthrough_surge', null, 6.0)
    expect(createdOscillators).toHaveLength(4)

    audio.playDialogueCue('trust_rupture', null, -3.0)
    audio.playDialogueCue('friction_damping', null, -0.8)
    audio.playInspectCue(true)
    audio.playVeilShiftCue('quasar_active')
    expect(createdOscillators.length).toBeGreaterThanOrEqual(10)
  })
})
