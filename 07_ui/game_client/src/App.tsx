import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import { ResonanceSandbox } from './components/ResonanceSandbox'
import { RoadThresholdWave } from './components/RoadThresholdWave'
import { mapSignalsToCueClasses, type CueType, type ResonanceSignals } from './lib/resonanceEvaluator'
import type { CodexEntry, GameState, NpcProfile, ShelfCharacter } from './types'

type DrawerId =
  | 'map'
  | 'quests'
  | 'inventory'
  | 'character'
  | 'codex'
  | 'chronicle'
  | 'trial'
  | 'market'
  | 'sandbox'
  | null

interface ChatLine {
  role: 'player' | 'npc'
  speaker: string
  text: string
}

function HeroPortrait({ npc }: { npc: NpcProfile }) {
  const [imgFailed, setImgFailed] = useState(false)
  useEffect(() => {
    setImgFailed(false)
  }, [npc.portrait_url])

  return (
    <div className="hero-portrait-stage">
      <div className="hero-portrait-frame" style={{ borderColor: npc.accent }}>
        {!imgFailed && npc.portrait_url ? (
          <img
            className="hero-portrait-img"
            src={npc.portrait_url}
            alt={npc.display_name}
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className="hero-sigil-fallback">
            <div className="hero-sigil-glyph" style={{ borderColor: npc.accent, color: npc.accent }}>
              {npc.display_name.slice(0, 1).toUpperCase()}
            </div>
            <div style={{ fontFamily: 'Cinzel, serif', fontSize: 11, letterSpacing: '0.2em', color: npc.accent }}>
              {npc.role}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [state, setState] = useState<GameState | null>(null)
  const [drawer, setDrawer] = useState<DrawerId>(null)
  const [selectedNpcId, setSelectedNpcId] = useState<string>('')
  const [inputText, setInputText] = useState('')
  const [chatHistory, setChatHistory] = useState<Record<string, ChatLine[]>>({})
  const [toast, setToast] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [codex, setCodex] = useState<CodexEntry[]>([])
  const [shelf, setShelf] = useState<ShelfCharacter[]>([])
  const [bindTargetNpc, setBindTargetNpc] = useState<string>('mira')
  const [lastSignals, setLastSignals] = useState<ResonanceSignals | null>(null)
  const [lastCueType, setLastCueType] = useState<CueType | null>(null)

  const notify = (msg: string) => {
    setToast(msg)
    window.setTimeout(() => setToast((curr) => (curr === msg ? null : curr)), 3600)
  }

  const bootstrap = () => {
    setLoadError(null)
    api
      .getState()
      .then((s) => {
        setState(s)
        if (s.npcs_here.length > 0) setSelectedNpcId(s.npcs_here[0].id)
      })
      .catch((err: Error) => {
        setLoadError(err.message || 'Unable to reach Veil Game Engine')
        notify(`API offline: ${err.message}`)
      })
    api.getCodex().then((r) => setCodex(r.entries || [])).catch(() => { })
    api.listLocalShelf().then((r) => setShelf(r.characters || [])).catch(() => { })
  }

  useEffect(() => {
    bootstrap()
  }, [])

  // Keyboard hotkeys for zero-chrome RPG drawers (M/J/I/P/C/L/Escape)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) {
        if (e.key === 'Escape') target.blur()
        return
      }
      const key = e.key.toLowerCase()
      if (key === 'escape') setDrawer(null)
      else if (key === 'm') setDrawer((d) => (d === 'map' ? null : 'map'))
      else if (key === 'j') setDrawer((d) => (d === 'quests' ? null : 'quests'))
      else if (key === 'i') setDrawer((d) => (d === 'inventory' ? null : 'inventory'))
      else if (key === 'p') setDrawer((d) => (d === 'character' ? null : 'character'))
      else if (key === 'c') {
        setDrawer((d) => (d === 'codex' ? null : 'codex'))
        api.getCodex().then((r) => setCodex(r.entries || [])).catch(() => { })
      } else if (key === 'l') setDrawer((d) => (d === 'chronicle' ? null : 'chronicle'))
      else if (key === 'x') setDrawer((d) => (d === 'sandbox' ? null : 'sandbox'))
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  const selectedNpc = useMemo(() => {
    if (!state) return null
    return state.npcs_here.find((n) => n.id === selectedNpcId) || state.npcs_here[0] || null
  }, [state, selectedNpcId])

  const handleTravel = async (locationId: string) => {
    setBusy(true)
    try {
      const res = await api.travel(locationId)
      setState(res.state)
      if (res.state.npcs_here.length > 0) setSelectedNpcId(res.state.npcs_here[0].id)
      notify(res.message)
      if (res.ok) setDrawer(null)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleAdvanceVeil = async () => {
    setBusy(true)
    try {
      const res = await api.advanceVeil()
      setState(res.state)
      notify(`Veil shifted to ${res.veil_state.replace('_', ' ')}`)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleSendDialogue = async (e: FormEvent, overrideText?: string) => {
    e.preventDefault()
    if (!selectedNpc) return
    const text = (overrideText ?? inputText).trim()
    if (!text) return
    setBusy(true)
    try {
      const res = await api.talk(selectedNpc.id, text)
      setState(res.state)
      if (res.signals) setLastSignals(res.signals)
      if (res.cue_type) setLastCueType(res.cue_type)
      setChatHistory((prev) => ({
        ...prev,
        [selectedNpc.id]: [
          ...(prev[selectedNpc.id] || []),
          { role: 'player', speaker: 'You', text },
          { role: 'npc', speaker: res.speaker, text: res.reply },
        ],
      }))
      setInputText('')
      const sign = res.resonance_delta >= 0 ? '+' : ''
      notify(`${sign}${res.resonance_delta.toFixed(1)} Resonance`)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleBuy = async (itemId: string) => {
    setBusy(true)
    try {
      const res = await api.buyItem(itemId)
      setState(res.state)
      notify(res.message)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleUseItem = async (itemId: string) => {
    setBusy(true)
    try {
      const res = await api.useItem(itemId)
      setState(res.state)
      notify(res.message)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleEncounter = async (encounterId: string, choiceId: string) => {
    setBusy(true)
    try {
      const res = await api.resolveEncounter(encounterId, choiceId)
      setState(res.state)
      notify(
        `${res.success ? 'SUCCESS' : 'RESISTED'} (Roll ${res.roll}+${res.modifier}=${res.total} vs DC ${res.dc})`,
      )
      if (res.success) setDrawer(null)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleQuickSave = async () => {
    if (!state) return
    setBusy(true)
    try {
      const label = `Day ${state.world.day_count} · ${state.world.current_location.name}`
      await api.saveGame('quicksave', label)
      const fresh = await api.getState()
      setState(fresh)
      notify(`Saved: ${label}`)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleLoadSave = async (slotId: string) => {
    setBusy(true)
    try {
      const res = await api.loadGame(slotId)
      setState(res.state)
      setChatHistory({})
      setInputText('')
      if (res.state.npcs_here.length > 0) setSelectedNpcId(res.state.npcs_here[0].id)
      setDrawer(null)
      notify(res.message)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleToggleParty = async (characterId: string) => {
    setBusy(true)
    try {
      const res = await api.toggleParty(characterId)
      setState(res.state)
      notify(res.message)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleBindPortrait = async (mediaKey: string) => {
    setBusy(true)
    try {
      const res = await api.bindPortrait(bindTargetNpc, mediaKey)
      setState(res.state)
      notify(`Bound portrait '${mediaKey}' to ${bindTargetNpc}`)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const handleResetSession = async () => {
    setBusy(true)
    try {
      const res = await api.resetSession()
      setState(res.state)
      setChatHistory({})
      setLastSignals(null)
      setLastCueType(null)
      if (res.state.npcs_here.length > 0) setSelectedNpcId(res.state.npcs_here[0].id)
      notify(res.message)
    } catch (err) {
      notify((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  if (!state) {
    return (
      <div className="veil-stage-shell" style={{ display: 'grid', placeItems: 'center', padding: 40 }}>
        <div className="card" style={{ maxWidth: 440, textAlign: 'center', zIndex: 5 }}>
          <div className="brand-title">THE VEIL</div>
          {loadError ? (
            <>
              <p className="scene-sub" style={{ marginTop: 10, color: 'var(--ember)' }}>
                Unable to connect to Veil Game Engine: {loadError}
              </p>
              <button type="button" className="btn btn-quasar" style={{ marginTop: 12 }} onClick={bootstrap}>
                Retry Connection
              </button>
            </>
          ) : (
            <p className="scene-sub" style={{ marginTop: 10 }}>
              Connecting to Veil Game Engine (<code>127.0.0.1:8765</code>)…
            </p>
          )}
        </div>
      </div>
    )
  }

  const { world, player } = state
  const activeNpcChat = selectedNpc ? chatHistory[selectedNpc.id] || [] : []
  const isSealedOut = player.resonance <= 0.0
  const isSuffocating = player.resonance < 100.0
  const isDegraded = player.resonance < 350.0

  return (
    <div className={`veil-stage-shell ${isSuffocating ? 'veil-suffocating' : ''}`}>
      {/* Layer 0: Atmospheric Veil Backdrop */}
      <div className={`backdrop-layer veil-${world.veil_state}`} />
      <div className="backdrop-grid" />

      {/* Layer 3a: Ghost Top HUD */}
      <header className={`ghost-header ${drawer ? 'pinned' : ''}`}>
        <div className="brand">
          <span className="brand-title">THE VEIL</span>
          <span className="brand-loc">
            {world.current_region.name} · {world.current_settlement.name}
          </span>
        </div>

        <div className="hud-pills">
          <span className="pill">
            Day <strong>{world.day_count}</strong> ({world.time_of_day})
          </span>
          <button
            type="button"
            className="pill veil-pill"
            onClick={handleAdvanceVeil}
            disabled={busy}
            title="Advance the Veil cycle (calm → still → storm → quasar_active)"
          >
            Veil: <strong>{world.veil_state.replace('_', ' ')}</strong> ↻
          </button>
          <span className="pill">
            Resonance <strong>{player.resonance.toFixed(1)}</strong> / 1000 ({player.resonance_tier.name})
          </span>
          <span className="pill">
            Lv <strong>{player.level}</strong>
          </span>
          <span className="pill" style={{ borderColor: 'var(--star)', color: 'var(--star)' }}>
            ◈ <strong>{world.echoes}</strong>
          </span>
        </div>
      </header>

      {/* Layer 3b: Ghost Right Navigation Rail */}
      <nav className={`ghost-rail ${drawer ? 'pinned' : ''}`} aria-label="Game drawers">
        <button
          type="button"
          className={`rail-btn ${drawer === 'map' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'map' ? null : 'map'))}
        >
          <span>World Map</span>
          <span className="hotkey">M</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'quests' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'quests' ? null : 'quests'))}
        >
          <span>Quest Journal ({state.quests.filter((q) => q.status === 'active').length})</span>
          <span className="hotkey">J</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'inventory' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'inventory' ? null : 'inventory'))}
        >
          <span>Relics & Pack ({state.inventory.length})</span>
          <span className="hotkey">I</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'character' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'character' ? null : 'character'))}
        >
          <span>Stats & Factions</span>
          <span className="hotkey">P</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'codex' ? 'active' : ''}`}
          onClick={() => {
            setDrawer((d) => (d === 'codex' ? null : 'codex'))
            api.getCodex().then((r) => setCodex(r.entries || [])).catch(() => { })
          }}
        >
          <span>Lore Codex</span>
          <span className="hotkey">C</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'chronicle' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'chronicle' ? null : 'chronicle'))}
        >
          <span>Chronicle</span>
          <span className="hotkey">L</span>
        </button>
        <button
          type="button"
          className={`rail-btn ${drawer === 'sandbox' ? 'active' : ''}`}
          onClick={() => setDrawer((d) => (d === 'sandbox' ? null : 'sandbox'))}
        >
          <span>Resonance Lab</span>
          <span className="hotkey">X</span>
        </button>
        <button type="button" className="btn btn-quasar" style={{ marginTop: 4 }} onClick={handleQuickSave}>
          Save Checkpoint
        </button>
      </nav>

      {/* Layer 1: Location Plate + Full-Bleed Character Stage */}
      <div className="location-title-plate">
        <div className="section-label" style={{ marginBottom: 2 }}>
          {world.current_settlement.type} · {world.current_location.district_id}
        </div>
        <h1>{world.current_location.name}</h1>
        <p className="location-subtitle">{world.current_location.surface_description}</p>
        {player.resonance >= 450.0 && (
          <div className="depth-whisper">
            <strong>Depth Perception:</strong> {world.current_location.depth_description}
          </div>
        )}
      </div>

      {selectedNpc && <HeroPortrait npc={selectedNpc} />}

      {/* Layer 2: Bottom Cinematic Dialogue & Scene Action Dock */}
      <main className="scene-stage">
        <section className="dialogue-dock">
          <div className="presence-strip">
            <div className="npc-chips">
              {state.npcs_here.map((npc) => (
                <button
                  key={npc.id}
                  type="button"
                  className={`npc-chip ${selectedNpc?.id === npc.id ? 'active' : ''}`}
                  onClick={() => setSelectedNpcId(npc.id)}
                >
                  <span style={{ color: npc.accent }}>●</span>
                  <span>{npc.display_name}</span>
                  {npc.in_party && <span style={{ color: 'var(--emerald)', fontSize: 10 }}>★</span>}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', gap: 6 }}>
              {state.encounters.length > 0 && (
                <button type="button" className="btn btn-bloom" onClick={() => setDrawer('trial')}>
                  ✦ Resonance Trial ({state.encounters.length})
                </button>
              )}
              {state.merchant && (
                <button type="button" className="btn btn-quasar" onClick={() => setDrawer('market')}>
                  ◈ Market
                </button>
              )}
            </div>
          </div>

          {selectedNpc && (
            <div
              className={`dock-card ${mapSignalsToCueClasses(lastSignals, lastCueType)}`}
              style={{ borderColor: selectedNpc.accent }}
            >
              <div className="dock-header">
                <div>
                  <span className="speaker-name" style={{ color: selectedNpc.accent }}>
                    {selectedNpc.display_name}
                  </span>
                  <span className="speaker-role">{selectedNpc.role}</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  {selectedNpc.bond !== undefined && (
                    <span className="pill" style={{ borderColor: 'var(--emerald)' }}>
                      Bond <strong>{selectedNpc.bond.toFixed(0)}</strong>
                    </span>
                  )}
                  <span className="pill">
                    Trust <strong>{selectedNpc.relationship.trust}</strong>
                  </span>
                  <span className="pill">
                    Suspicion <strong>{selectedNpc.relationship.suspicion}</strong>
                  </span>
                  {selectedNpc.can_join_party && (
                    <button
                      type="button"
                      className={`btn ${selectedNpc.in_party ? 'btn-quasar' : ''}`}
                      style={{ padding: '4px 9px', fontSize: 11 }}
                      disabled={busy}
                      onClick={() => handleToggleParty(selectedNpc.id)}
                    >
                      {selectedNpc.in_party ? '✓ In Party' : '+ Recruit'}
                    </button>
                  )}
                </div>
              </div>

              <div className="dialogue-feed">
                {activeNpcChat.length === 0 ? (
                  <div className="msg-bubble">
                    <strong style={{ color: selectedNpc.accent }}>{selectedNpc.display_name}:</strong>{' '}
                    {selectedNpc.greeting}
                  </div>
                ) : (
                  activeNpcChat.map((line, idx) => (
                    <div key={idx} className={`msg-bubble ${line.role}`}>
                      <strong>{line.speaker}:</strong> {line.text}
                    </div>
                  ))
                )}
              </div>

              {isSealedOut ? (
                <div className="card" style={{ borderColor: 'var(--text-muted)', textAlign: 'center' }}>
                  <p className="scene-sub" style={{ marginBottom: 8 }}>
                    The Veil has closed around this frequency (0.0). The town no longer answers.
                  </p>
                  <button type="button" className="btn btn-quasar" disabled={busy} onClick={handleResetSession}>
                    Begin New Frequency
                  </button>
                </div>
              ) : (
                <>
                  {isSuffocating && (
                    <div className="depth-whisper" style={{ borderColor: 'var(--ember)', color: 'var(--star)' }}>
                      The Veil is suffocating your voice (&lt; 100.0). Use an Echo Shard or Vial of Memory Ash to cross.
                    </div>
                  )}

                  <div className="dialogue-choices">
                    {isDegraded ? (
                      <button
                        type="button"
                        className="btn"
                        disabled={busy}
                        onClick={(e) => handleSendDialogue(e, 'What places are still open around the plaza?')}
                      >
                        Is anything open nearby?
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="btn"
                          disabled={busy}
                          onClick={(e) => handleSendDialogue(e, 'What lies beneath the Prism surface here?')}
                        >
                          Ask about the Veil
                        </button>
                        <button
                          type="button"
                          className="btn btn-quasar"
                          disabled={busy}
                          onClick={(e) => handleSendDialogue(e, 'Tell me the truth about the Dark Quasar and your role.')}
                        >
                          Probe deeper truth
                        </button>
                      </>
                    )}
                  </div>

                  <form className="dialogue-form" onSubmit={handleSendDialogue}>
                    <input
                      className="text-input"
                      placeholder={
                        isSuffocating
                          ? 'Your voice scatters into static…'
                          : `Speak to ${selectedNpc.display_name}…`
                      }
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      disabled={busy}
                    />
                    <button type="submit" className="btn" disabled={busy || !inputText.trim()}>
                      Send
                    </button>
                  </form>
                </>
              )}
            </div>
          )}
        </section>
      </main>

      {/* Layer 4: Slide-Over Drawers */}
      {drawer && (
        <div className="drawer-backdrop" onClick={() => setDrawer(null)}>
          <aside className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="drawer-title">
                {drawer === 'map' && 'World & Town Map'}
                {drawer === 'quests' && 'Quest Journal'}
                {drawer === 'inventory' && 'Relics & Pack'}
                {drawer === 'character' && 'Stats, Party & Factions'}
                {drawer === 'codex' && 'Lore Codex'}
                {drawer === 'chronicle' && 'Chronicle & Memory'}
                {drawer === 'trial' && 'Resonance Trial'}
                {drawer === 'market' && (state.merchant?.name || 'Market')}
                {drawer === 'sandbox' && 'Resonance Psychometric Sandbox'}
              </div>
              <button type="button" className="btn" onClick={() => setDrawer(null)}>
                Close [Esc]
              </button>
            </div>

            {drawer === 'map' && (
              <>
                <div className="map-canvas">
                  <svg width="100%" height="100%" style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
                    {world.connections.map((edge, idx) => {
                      const a = world.locations.find((l) => l.id === edge.from)
                      const b = world.locations.find((l) => l.id === edge.to)
                      if (!a || !b) return null
                      return (
                        <line
                          key={idx}
                          x1={`${a.map_coords.x}%`}
                          y1={`${a.map_coords.y}%`}
                          x2={`${b.map_coords.x}%`}
                          y2={`${b.map_coords.y}%`}
                          stroke="rgba(168, 85, 247, 0.40)"
                          strokeWidth={1.5}
                          strokeDasharray={a.unlocked && b.unlocked ? undefined : '4 4'}
                        />
                      )
                    })}
                  </svg>
                  {world.locations.map((loc) => (
                    <button
                      key={loc.id}
                      type="button"
                      className={`map-node ${loc.is_current ? 'current' : ''} ${!loc.unlocked ? 'locked' : ''}`}
                      style={{ left: `${loc.map_coords.x}%`, top: `${loc.map_coords.y}%` }}
                      onClick={() => handleTravel(loc.id)}
                      disabled={busy}
                      title={loc.unlocked ? `Travel to ${loc.name}` : loc.lock_reason}
                    >
                      <div>{loc.name}</div>
                      <div style={{ fontSize: 9, color: 'var(--text-dim)' }}>
                        {loc.settlement_name} {!loc.unlocked ? '🔒' : ''}
                      </div>
                    </button>
                  ))}
                </div>

                <div className="grid-cards">
                  {world.locations.map((loc) => (
                    <div key={loc.id} className="card">
                      <div style={{ fontWeight: 600 }}>{loc.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--quasar-bright)' }}>{loc.settlement_name}</div>
                      {!loc.unlocked && loc.lock_reason.includes('Resonance') ? (
                        <div style={{ margin: '8px 0' }}>
                          <RoadThresholdWave
                            roadName={loc.name}
                            currentResonance={player.resonance}
                            requiredResonance={parseFloat(loc.lock_reason.match(/(\d+(?:\.\d+)?)/)?.[1] ?? '500.0')}
                          />
                        </div>
                      ) : (
                        <p className="scene-sub" style={{ margin: '6px 0' }}>
                          {loc.unlocked ? loc.surface_description : loc.lock_reason}
                        </p>
                      )}
                      <button
                        type="button"
                        className="btn"
                        disabled={busy || !loc.unlocked || loc.is_current}
                        onClick={() => handleTravel(loc.id)}
                      >
                        {loc.is_current ? 'Here' : loc.unlocked ? 'Travel' : 'Locked'}
                      </button>
                    </div>
                  ))}
                </div>
              </>
            )}

            {drawer === 'quests' &&
              state.quests.map((q) => (
                <div key={q.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong style={{ color: q.status === 'completed' ? 'var(--emerald)' : 'var(--bloom)' }}>
                      {q.title}
                    </strong>
                    <span className="pill">
                      {q.arc} · {q.status}
                    </span>
                  </div>
                  <p className="scene-sub" style={{ margin: '6px 0' }}>
                    {q.summary}
                  </p>
                  <div style={{ fontSize: 12, color: 'var(--quasar-bright)' }}>Objective: {q.current_objective}</div>
                </div>
              ))}

            {drawer === 'inventory' && (
              <div className="grid-cards">
                {state.inventory.map((item) => (
                  <div key={item.id} className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>
                        {item.name} ×{item.quantity}
                      </strong>
                      <span style={{ fontSize: 11, color: 'var(--star)' }}>{item.rarity}</span>
                    </div>
                    <p className="scene-sub" style={{ margin: '6px 0' }}>
                      {item.active_description}
                    </p>
                    <button type="button" className="btn btn-quasar" disabled={busy} onClick={() => handleUseItem(item.id)}>
                      {item.equippable ? (item.equipped ? 'Unequip' : 'Equip') : 'Use'}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {drawer === 'codex' &&
              codex.map((entry) => (
                <div key={entry.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <strong style={{ color: entry.unlocked ? 'var(--quasar-bright)' : 'var(--text-muted)' }}>
                      {entry.title}
                    </strong>
                    <span className="pill">
                      {entry.category} · {entry.unlocked ? 'Unlocked' : `Res >= ${entry.min_resonance}`}
                    </span>
                  </div>
                  <pre
                    style={{
                      whiteSpace: 'pre-wrap',
                      fontFamily: 'inherit',
                      fontSize: 11,
                      color: entry.unlocked ? 'var(--text-dim)' : 'var(--text-muted)',
                    }}
                  >
                    {entry.excerpt}
                  </pre>
                </div>
              ))}

            {drawer === 'chronicle' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {state.recent_logs.length === 0 ? (
                  <p className="scene-sub">The Veil awaits your first step.</p>
                ) : (
                  state.recent_logs.map((entry) => (
                    <div key={entry.id} className="log-item">
                      <strong style={{ color: 'var(--veil-bright)' }}>[{entry.agent_id}]</strong> {entry.content}
                    </div>
                  ))
                )}
              </div>
            )}

            {drawer === 'trial' &&
              state.encounters.map((enc) => (
                <div key={enc.id} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <strong style={{ color: 'var(--bloom)', fontSize: 15 }}>{enc.title}</strong>
                  <p className="scene-sub">{enc.description}</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {enc.choices.map((ch) => (
                      <button
                        key={ch.id}
                        type="button"
                        className="btn btn-quasar"
                        disabled={busy}
                        onClick={() => handleEncounter(enc.id, ch.id)}
                      >
                        {ch.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}

            {drawer === 'market' && state.merchant && (
              <div className="grid-cards">
                {state.merchant.items.map((item) => (
                  <div key={item.id} className="card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                      <strong>{item.name}</strong>
                      <span style={{ color: 'var(--star)' }}>◈ {item.value_echoes}</span>
                    </div>
                    <p className="scene-sub" style={{ marginBottom: 8 }}>
                      {item.prism_description}
                    </p>
                    <button
                      type="button"
                      className="btn"
                      disabled={busy || world.echoes < item.value_echoes}
                      onClick={() => handleBuy(item.id)}
                    >
                      Purchase
                    </button>
                  </div>
                ))}
              </div>
            )}

            {drawer === 'sandbox' && <ResonanceSandbox />}

            {drawer === 'character' && (
              <>
                <div className="card">
                  <div className="section-label">Psychometric Attributes</div>
                  <div className="grid-cards">
                    {(['clarity', 'empathy', 'resolve', 'perception', 'veil_attunement'] as const).map((k) => (
                      <div key={k} className="card">
                        <div className="section-label" style={{ marginBottom: 2 }}>
                          {k.replace('_', ' ')}
                        </div>
                        <div style={{ fontFamily: 'Cinzel Decorative, serif', fontSize: 22 }}>
                          {player[k]}
                          {player.bonuses[k] ? (
                            <span style={{ fontSize: 12, color: 'var(--emerald)', marginLeft: 6 }}>
                              +{player.bonuses[k]}
                            </span>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {world.active_party && world.active_party.length > 0 && (
                  <div className="card">
                    <div className="section-label">Active Party ({world.active_party.length}/3)</div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {world.active_party.map((pid) => (
                        <span key={pid} className="pill" style={{ borderColor: 'var(--bloom)', color: 'var(--text)' }}>
                          {pid}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="card">
                  <div className="section-label">Factions</div>
                  <div className="grid-cards">
                    {state.factions.map((f) => (
                      <div key={f.id} className="card">
                        <strong>{f.name}</strong>
                        <div style={{ fontSize: 11, color: 'var(--quasar-bright)' }}>
                          {f.rank} ({f.reputation})
                        </div>
                        <p className="scene-sub" style={{ marginTop: 4 }}>
                          {f.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>

                {state.ending_status && (
                  <div className="card">
                    <div className="section-label">Veil Convergence · Ending Trajectory</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <strong
                        style={{
                          color:
                            state.ending_status.trajectory === 'true_ending_ready' ? 'var(--emerald)' : 'var(--bloom)',
                        }}
                      >
                        {state.ending_status.trajectory.replace(/_/g, ' ').toUpperCase()}
                      </strong>
                      <span className="pill">Max Sister Trust: {state.ending_status.max_sister_trust}</span>
                    </div>
                    <p className="scene-sub" style={{ marginBottom: 8 }}>
                      {state.ending_status.summary}
                    </p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {Object.entries(state.ending_status.criteria).map(([key, met]) => (
                        <span
                          key={key}
                          className="pill"
                          style={{
                            borderColor: met ? 'var(--emerald)' : 'var(--glass-border)',
                            color: met ? 'var(--emerald)' : 'var(--text-dim)',
                          }}
                        >
                          {met ? '✓' : '○'} {key.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {shelf.length > 0 && (
                  <div className="card">
                    <div className="section-label">Local Portrait Binder ({shelf.length} shelf assets)</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                      <span className="scene-sub">Bind to NPC:</span>
                      <select
                        className="text-input"
                        style={{ maxWidth: 200 }}
                        value={bindTargetNpc}
                        onChange={(e) => setBindTargetNpc(e.target.value)}
                      >
                        {state.npcs_here.map((n) => (
                          <option key={n.id} value={n.id}>
                            {n.display_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {shelf.slice(0, 12).map((ch) => (
                        <button
                          key={ch.id}
                          type="button"
                          className="btn"
                          disabled={busy}
                          onClick={() => handleBindPortrait(ch.id)}
                        >
                          {ch.display_name}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="card">
                  <div className="section-label">Save Slots</div>
                  {state.saves.length === 0 ? (
                    <p className="scene-sub">No saved checkpoints yet. Click "Save Checkpoint" in the ghost rail.</p>
                  ) : (
                    state.saves.map((s) => (
                      <div
                        key={s.slot_id}
                        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}
                      >
                        <span>{s.label}</span>
                        <button type="button" className="btn" onClick={() => handleLoadSave(s.slot_id)}>
                          Load
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}
          </aside>
        </div>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
