import React, { useState } from 'react'
import { useResonanceSession } from '../lib/useResonanceSession'
import { RoadThresholdWave } from './RoadThresholdWave'

const SAMPLE_NPCS = {
  warden: {
    id: 'npc_warden',
    name: 'Stillward Warden',
    initialStance: 'hostile' as const,
    openingLine: 'Step back from the Listening Wall. The fog already took enough voices tonight.',
    unlockedTokens: ['quasar', 'fracture', 'lanterns'],
  },
  mira: {
    id: 'npc_mira',
    name: 'Mira',
    initialStance: 'guarded' as const,
    openingLine: 'The Prism is warm tonight, though most visitors pass right through without noticing.',
    unlockedTokens: ['prism', 'memory', 'shadow'],
  },
}

export const ResonanceSandbox: React.FC = () => {
  const {
    session,
    lastEvaluation,
    membrane,
    submitTalk,
    advanceNonTalkTurn,
    useConsumableOrTrial,
  } = useResonanceSession()

  const [selectedNpcKey, setSelectedNpcKey] = useState<'warden' | 'mira'>('warden')
  const [inputText, setInputText] = useState('')
  const [log, setLog] = useState<Array<{ sender: string; text: string; meta?: string }>>([
    {
      sender: SAMPLE_NPCS.warden.name,
      text: SAMPLE_NPCS.warden.openingLine,
      meta: 'Stance: hostile',
    },
  ])

  const activeNpc = SAMPLE_NPCS[selectedNpcKey]
  const currentEncounter = session.encounters[activeNpc.id]
  const currentStance = currentEncounter?.currentStance ?? activeNpc.initialStance

  const handleSelectNpc = (key: 'warden' | 'mira') => {
    setSelectedNpcKey(key)
    const npc = SAMPLE_NPCS[key]
    setLog([{ sender: npc.name, text: npc.openingLine, meta: `Stance: ${npc.initialStance}` }])
  }

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || session.isSealedOut) return

    const lastNpcEntry = [...log].reverse().find((m) => m.sender === activeNpc.name)
    const npcLastLine = lastNpcEntry?.text ?? activeNpc.openingLine

    const result = submitTalk(
      activeNpc.id,
      npcLastLine,
      inputText,
      activeNpc.initialStance,
      activeNpc.unlockedTokens,
    )

    const { evaluation, renderedPlayerText, nextState } = result
    const sign = evaluation.delta >= 0 ? '+' : ''

    let simulatedReply = 'The mist drifts between us without answering.'
    if (nextState.resonance < 100.0) {
      simulatedReply = '...'
    } else if (evaluation.cueType === 'breakthrough_surge') {
      simulatedReply =
        'You stayed when everyone else turned away. Listen closely—the Prism isn’t broken, it’s waiting.'
    } else if (evaluation.cueType === 'saved_face_stabilized') {
      simulatedReply =
        'You don’t push back like the others. Keep your voice steady if you want to stay near the wall.'
    } else if (evaluation.cueType === 'friction_damping') {
      simulatedReply = 'Save your breath. Empty words don’t carry here.'
    } else if (nextState.resonance >= 800.0 && nextState.veilState === 'quasar_active') {
      simulatedReply = 'The sky is open—you can hear my true name now beneath the quasar hum.'
    } else {
      simulatedReply = 'The air feels thinner when you speak like that. What else do you remember?'
    }

    setLog((prev) => [
      ...prev,
      {
        sender: 'Visitor',
        text: renderedPlayerText,
        meta: `${sign}${evaluation.delta.toFixed(2)} (${evaluation.cueType})`,
      },
      {
        sender: activeNpc.name,
        text: simulatedReply,
        meta: `Stance: ${evaluation.updatedEncounter.currentStance} · Bond ${(evaluation.updatedEncounter.npcBond ?? 0).toFixed(1)}`,
      },
    ])
    setInputText('')
  }

  return (
    <div style={{ ...(membrane.cssVars as React.CSSProperties), display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div className="section-label" style={{ marginBottom: 2 }}>
            Resonance Psychometric Sandbox
          </div>
          <div className="scene-sub">
            Grace Window:{' '}
            {session.turnsTaken < 5 && !session.hasCrossedFirstThreshold ? 'Active (350.0 Floor)' : 'Dissolved'}
            {' · '}NPC Bond: {(currentEncounter?.npcBond ?? 0).toFixed(1)}/100
            {' · '}Contrib: {(currentEncounter?.townContribution ?? 0).toFixed(1)}/50
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontFamily: 'Cinzel Decorative, serif', fontSize: 20, color: 'var(--star)' }}>
            {membrane.percentDisplay}
          </div>
          <div style={{ fontSize: 10, letterSpacing: '0.18em', color: 'var(--quasar-bright)' }}>
            {membrane.tierName.toUpperCase()}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
        <button
          type="button"
          className={`btn ${selectedNpcKey === 'warden' ? 'btn-quasar' : ''}`}
          onClick={() => handleSelectNpc('warden')}
        >
          Warden (Hostile Arc)
        </button>
        <button
          type="button"
          className={`btn ${selectedNpcKey === 'mira' ? 'btn-quasar' : ''}`}
          onClick={() => handleSelectNpc('mira')}
        >
          Mira (Guarded Arc)
        </button>
        <button type="button" className="btn" onClick={() => useConsumableOrTrial({ itemId: 'echo_shard' })}>
          + Echo Shard (+6.0)
        </button>
        <button type="button" className="btn" onClick={() => useConsumableOrTrial({ itemId: 'vial_of_memory_ash' })}>
          + Memory Ash (+10.0)
        </button>
        <button type="button" className="btn btn-bloom" onClick={() => advanceNonTalkTurn()}>
          Idle/Travel ({session.turnsSinceLastTalk}/3)
        </button>
      </div>

      {lastEvaluation && (
        <div className="card" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, fontSize: 11 }}>
          <span style={{ color: lastEvaluation.signals.mirroredNpc ? 'var(--emerald)' : 'var(--text-muted)' }}>
            [Mirror +0.6]
          </span>
          <span style={{ color: lastEvaluation.signals.openInquiry ? 'var(--emerald)' : 'var(--text-muted)' }}>
            [Inquiry +0.5]
          </span>
          <span style={{ color: lastEvaluation.signals.interiority ? 'var(--emerald)' : 'var(--text-muted)' }}>
            [Interiority +0.6]
          </span>
          <span style={{ color: lastEvaluation.signals.thematicInSentence ? 'var(--emerald)' : 'var(--text-muted)' }}>
            [Thematic +0.6]
          </span>
          <span style={{ color: lastEvaluation.signals.sustainedCadence ? 'var(--emerald)' : 'var(--text-muted)' }}>
            [Length&gt;45 +0.3]
          </span>
          {lastEvaluation.signals.npcTaperApplied && (
            <span style={{ color: 'var(--star)' }}>[Town Taper 0.15×]</span>
          )}
          {lastEvaluation.signals.frictionType !== 'none' && (
            <span style={{ color: 'var(--ember)' }}>[Friction: {lastEvaluation.signals.frictionType}]</span>
          )}
          {lastEvaluation.cueType === 'breakthrough_surge' && (
            <span style={{ color: 'var(--star)', fontWeight: 600 }}>[BREAKTHROUGH SURGE +3.5]</span>
          )}
        </div>
      )}

      <div className="card dialogue-feed" style={{ maxHeight: 200 }}>
        {log.map((entry, idx) => (
          <div key={idx} className={`msg-bubble ${entry.sender === 'Visitor' ? 'player' : ''}`}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 2 }}>
              <strong style={{ color: entry.sender === 'Visitor' ? 'var(--quasar-bright)' : 'var(--star)' }}>
                {entry.sender}
              </strong>
              {entry.meta && <span style={{ color: 'var(--text-muted)' }}>{entry.meta}</span>}
            </div>
            <div>{entry.text}</div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSend} className="dialogue-form">
        <input
          type="text"
          className="text-input"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={session.isSealedOut}
          placeholder={
            session.isSealedOut
              ? 'The Veil has sealed you out (0.0).'
              : `Speak to ${activeNpc.name} (Stance: ${currentStance})…`
          }
        />
        <button type="submit" className="btn btn-quasar" disabled={session.isSealedOut || !inputText.trim()}>
          Speak
        </button>
      </form>

      <div className="grid-cards">
        <RoadThresholdWave
          roadName="Listening Wall"
          currentResonance={session.resonance}
          requiredResonance={550.0}
        />
        <RoadThresholdWave
          roadName="The Hollow"
          currentResonance={session.resonance}
          requiredResonance={750.0}
        />
      </div>
    </div>
  )
}
