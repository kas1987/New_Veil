import type { CueType, ResonanceSignals } from './resonanceEvaluator'

type AudioCtxCtor = typeof AudioContext

function resolveAudioContext(): AudioCtxCtor | null {
  if (typeof window === 'undefined') return null
  const win = window as unknown as {
    AudioContext?: AudioCtxCtor
    webkitAudioContext?: AudioCtxCtor
  }
  return win.AudioContext ?? win.webkitAudioContext ?? null
}

/**
 * Procedural Web Audio synthesizer for subconscious Veil Resonance micro-cues
 * (per 12_metaphysics/RESONANCE.md). Muted by default and safe under jsdom/headless browsers.
 */
export class VeilAudioEngine {
  private enabled = false
  private ctx: AudioContext | null = null

  isEnabled(): boolean {
    return this.enabled
  }

  setEnabled(next: boolean): void {
    this.enabled = next
    if (next) {
      const ctx = this.ensureContext()
      if (ctx && ctx.state === 'suspended') {
        void ctx.resume().catch(() => {})
      }
    }
  }

  private ensureContext(): AudioContext | null {
    if (!this.enabled) return null
    if (this.ctx) return this.ctx
    const Ctor = resolveAudioContext()
    if (!Ctor) return null
    try {
      this.ctx = new Ctor()
      return this.ctx
    } catch {
      return null
    }
  }

  private playTone(
    freqStart: number,
    durationSec: number,
    type: OscillatorType = 'sine',
    peakGain = 0.045,
    delaySec = 0,
    freqEnd?: number,
  ): void {
    const ctx = this.ensureContext()
    if (!ctx) return
    try {
      const now = ctx.currentTime + delaySec
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = type
      osc.frequency.setValueAtTime(freqStart, now)
      if (freqEnd !== undefined) {
        osc.frequency.exponentialRampToValueAtTime(Math.max(20, freqEnd), now + durationSec)
      }
      gain.gain.setValueAtTime(0.0001, now)
      gain.gain.linearRampToValueAtTime(peakGain, now + 0.025)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + durationSec)
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.start(now)
      osc.stop(now + durationSec + 0.02)
    } catch {
      // Ignore audio hardware restrictions gracefully
    }
  }

  private playChord(freqs: number[], durationSec = 0.55, type: OscillatorType = 'triangle', peakGain = 0.03): void {
    freqs.forEach((f, idx) => {
      this.playTone(f, durationSec, type, peakGain, idx * 0.035)
    })
  }

  playDialogueCue(cueType: CueType | null, signals: ResonanceSignals | null, delta: number): void {
    if (!this.enabled) return
    if (cueType === 'breakthrough_surge') {
      this.playChord([261.63, 392.0, 587.33, 659.25], 0.8, 'sine', 0.035)
      return
    }
    if (cueType === 'trust_rupture') {
      this.playTone(110.0, 0.36, 'sawtooth', 0.035, 0, 78.0)
      return
    }
    if (cueType === 'friction_damping') {
      this.playTone(130.0, 0.22, 'triangle', 0.03, 0, 92.0)
      return
    }
    if (cueType === 'saturation_cap') {
      this.playChord([293.66, 440.0, 739.99], 0.6, 'sine', 0.03)
      return
    }
    if (cueType === 'saved_face_stabilized') {
      this.playChord([196.0, 293.66], 0.45, 'sine', 0.03)
      return
    }
    if (delta > 0) {
      if (signals?.interiority || signals?.thematicInSentence) {
        this.playTone(587.33, 0.34, 'sine', 0.032)
      } else if (signals?.openInquiry) {
        this.playTone(440.0, 0.28, 'sine', 0.03, 0, 523.25)
      } else if (signals?.mirroredNpc) {
        this.playTone(392.0, 0.26, 'sine', 0.028)
      } else if (signals?.sustainedCadence) {
        this.playTone(146.83, 0.4, 'sine', 0.025)
      } else {
        this.playTone(329.63, 0.22, 'sine', 0.022)
      }
    }
  }

  playInspectCue(isDqInsight: boolean): void {
    if (!this.enabled) return
    if (isDqInsight) {
      this.playChord([329.63, 493.88, 659.25], 0.65, 'sine', 0.032)
    } else {
      this.playTone(523.25, 0.22, 'sine', 0.024)
    }
  }

  playVeilShiftCue(veilState: string): void {
    if (!this.enabled) return
    if (veilState === 'quasar_active') {
      this.playTone(98.0, 0.65, 'triangle', 0.04, 0, 146.83)
    } else if (veilState === 'storm') {
      this.playTone(164.81, 0.4, 'sawtooth', 0.028, 0, 123.47)
    } else if (veilState === 'still') {
      this.playTone(293.66, 0.45, 'sine', 0.025)
    } else {
      this.playTone(261.63, 0.38, 'sine', 0.025, 0, 329.63)
    }
  }
}

export const veilAudio = new VeilAudioEngine()
