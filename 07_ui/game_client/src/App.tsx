import { FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import type { CodexEntry, GameState, NpcProfile, ShelfCharacter } from './types'

type Tab = 'scene' | 'map' | 'quests' | 'inventory' | 'codex' | 'character'

interface ChatLine {
  role: 'player' | 'npc'
  speaker: string
  text: string
}

function NpcAvatar({ npc }: { npc: NpcProfile }) {
  const [imgFailed, setImgFailed] = useState(false)
  if (!imgFailed && npc.portrait_url) {
    return (
      <img
        className="npc-avatar"
        src={npc.portrait_url}
        alt={npc.display_name}
        style={{ borderColor: npc.accent }}
        onError={() => setImgFailed(true)}
      />
    )
  }
  return (
    <div
      className="npc-avatar"
      style={{ borderColor: npc.accent, color: npc.accent }}
      aria-label={npc.display_name}
    >
      {npc.display_name.slice(0, 1).toUpperCase()}
    </div>
  )
}

export default function App() {
  const [state, setState] = useState<GameState | null>(null)
  const [tab, setTab] = useState<Tab>('scene')
  const [selectedNpcId, setSelectedNpcId] = useState<string>('')
  const [inputText, setInputText] = useState('')
  const [chatHistory, setChatHistory] = useState<Record<string, ChatLine[]>>({})
  const [toast, setToast] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [codex, setCodex] = useState<CodexEntry[]>([])
  const [shelf, setShelf] = useState<ShelfCharacter[]>([])
  const [bindTargetNpc, setBindTargetNpc] = useState<string>('mira')

  const notify = (msg: string) => {
    setToast(msg)
    window.setTimeout(() => setToast((curr) => (curr === msg ? null : curr)), 3600)
  }

  useEffect(() => {
    api
      .getState()
      .then((s) => {
        setState(s)
        if (s.npcs_here.length > 0) setSelectedNpcId(s.npcs_here[0].id)
      })
      .catch((err: Error) => notify(`API offline: ${err.message}`))
    api.getCodex().then((r) => setCodex(r.entries || [])).catch(() => {})
    api.listLocalShelf().then((r) => setShelf(r.characters || [])).catch(() => {})
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
      if (res.ok) setTab('scene')
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
      setChatHistory((prev) => ({
        ...prev,
        [selectedNpc.id]: [
          ...(prev[selectedNpc.id] || []),
          { role: 'player', speaker: 'You', text },
          { role: 'npc', speaker: res.speaker, text: res.reply },
        ],
      }))
      setInputText('')
      notify(`+${res.resonance_delta.toFixed(3)} Resonance`)
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
    } finally {
      setBusy(false)
    }
  }

  const handleQuickSave = async () => {
    if (!state) return
    const label = `Day ${state.world.day_count} · ${state.world.current_location.name}`
    await api.saveGame('quicksave', label)
    const fresh = await api.getState()
    setState(fresh)
    notify(`Saved: ${label}`)
  }

  const handleLoadSave = async (slotId: string) => {
    const res = await api.loadGame(slotId)
    setState(res.state)
    notify(res.message)
  }

  const handleToggleParty = async (characterId: string) => {
    setBusy(true)
    try {
      const res = await api.toggleParty(characterId)
      setState(res.state)
      notify(res.message)
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
    } finally {
      setBusy(false)
    }
  }

  if (!state) {
    return (
      <div className="veil-shell" style={{ placeItems: 'center', padding: 40 }}>
        <div className="card" style={{ maxWidth: 440, textAlign: 'center' }}>
          <div className="brand-title">THE VEIL</div>
          <p className="scene-sub" style={{ marginTop: 10 }}>
            Connecting to Veil Game Engine (<code>127.0.0.1:8765</code>)…
          </p>
        </div>
      </div>
    )
  }

  const { world, player } = state
  const activeNpcChat = selectedNpc ? chatHistory[selectedNpc.id] || [] : []

  return (
    <div className="veil-shell">
      <div className={`glow-ring veil-${world.veil_state}`} />

      {/* Top HUD */}
      <header className="hud-header">
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
            Resonance <strong>{(player.resonance * 100).toFixed(0)}%</strong> ({player.resonance_tier.name})
          </span>
          <span className="pill">
            Lv <strong>{player.level}</strong> ({player.xp} XP)
          </span>
          <span className="pill" style={{ borderColor: 'var(--star)', color: 'var(--star)' }}>
            ◈ <strong>{world.echoes}</strong> Echoes
          </span>
        </div>
      </header>

      {/* Main 3-Column RPG Layout */}
      <div className="workspace">
        {/* Left Navigation Rail */}
        <aside className="card nav-rail">
          <div className="section-label">Navigation</div>
          <button
            type="button"
            className={`nav-btn ${tab === 'scene' ? 'active' : ''}`}
            onClick={() => setTab('scene')}
          >
            ◈ Scene & Dialogue
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === 'map' ? 'active' : ''}`}
            onClick={() => setTab('map')}
          >
            ✦ World & Town Map
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === 'quests' ? 'active' : ''}`}
            onClick={() => setTab('quests')}
          >
            ✧ Quest Journal ({state.quests.filter((q) => q.status === 'active').length})
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === 'inventory' ? 'active' : ''}`}
            onClick={() => setTab('inventory')}
          >
            ❖ Relics & Pack ({state.inventory.length})
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === 'codex' ? 'active' : ''}`}
            onClick={() => {
              setTab('codex')
              api.getCodex().then((r) => setCodex(r.entries || [])).catch(() => {})
            }}
          >
            ✦ Lore Codex
          </button>
          <button
            type="button"
            className={`nav-btn ${tab === 'character' ? 'active' : ''}`}
            onClick={() => setTab('character')}
          >
            ◎ Stats & Factions
          </button>

          {world.active_party && world.active_party.length > 0 && (
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--glass-border)' }}>
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

          <div style={{ marginTop: 'auto', paddingTop: 14, borderTop: '1px solid var(--glass-border)' }}>
            <button type="button" className="btn btn-quasar" style={{ width: '100%' }} onClick={handleQuickSave}>
              Save Checkpoint
            </button>
          </div>
        </aside>

        {/* Center Interactive Stage */}
        <main className="main-stage">
          {tab === 'scene' && (
            <>
              <section className="card scene-banner">
                <div className="section-label">
                  {world.current_settlement.type} · {world.current_location.district_id}
                </div>
                <div className="scene-title">{world.current_location.name}</div>
                <p className="scene-sub">{world.current_location.surface_description}</p>
                {player.resonance >= 0.45 && (
                  <div className="depth-whisper">
                    <strong>Depth Perception:</strong> {world.current_location.depth_description}
                  </div>
                )}
              </section>

              {/* Present NPCs */}
              <section>
                <div className="section-label">Present Here ({state.npcs_here.length})</div>
                <div className="npc-grid">
                  {state.npcs_here.map((npc) => (
                    <div
                      key={npc.id}
                      className={`card npc-card ${selectedNpc?.id === npc.id ? 'selected' : ''}`}
                      onClick={() => setSelectedNpcId(npc.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => e.key === 'Enter' && setSelectedNpcId(npc.id)}
                    >
                      <div className="npc-head">
                        <NpcAvatar npc={npc} />
                        <div>
                          <div style={{ fontWeight: 600, color: npc.accent }}>{npc.display_name}</div>
                          <div style={{ fontSize: 11, color: 'var(--text-dim)' }}>{npc.role}</div>
                        </div>
                      </div>
                      <div className="bar-row">
                        <span>Trust</span>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${npc.relationship.trust}%`, background: 'var(--emerald)' }} />
                        </div>
                        <span>{npc.relationship.trust}</span>
                      </div>
                      <div className="bar-row">
                        <span>Suspicion</span>
                        <div className="bar-track">
                          <div className="bar-fill" style={{ width: `${npc.relationship.suspicion}%`, background: 'var(--ember)' }} />
                        </div>
                        <span>{npc.relationship.suspicion}</span>
                      </div>
                      {npc.can_join_party && (
                        <button
                          type="button"
                          className={`btn ${npc.in_party ? 'btn-quasar' : ''}`}
                          style={{ marginTop: 4, fontSize: 11, padding: '4px 8px' }}
                          disabled={busy}
                          onClick={(e) => {
                            e.stopPropagation()
                            handleToggleParty(npc.id)
                          }}
                        >
                          {npc.in_party ? '✓ In Party' : '+ Recruit'}
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </section>

              {/* Active Dialogue */}
              {selectedNpc && (
                <section className="card dialogue-box">
                  <div className="section-label">Conversing with {selectedNpc.display_name}</div>
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

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
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
                  </div>

                  <form className="dialogue-form" onSubmit={handleSendDialogue}>
                    <input
                      className="text-input"
                      placeholder={`Speak to ${selectedNpc.display_name}…`}
                      value={inputText}
                      onChange={(e) => setInputText(e.target.value)}
                      disabled={busy}
                    />
                    <button type="submit" className="btn" disabled={busy || !inputText.trim()}>
                      Send
                    </button>
                  </form>
                </section>
              )}

              {/* Encounters / Resonance Trials */}
              {state.encounters.length > 0 && (
                <section className="card">
                  <div className="section-label">Resonance Trial Available</div>
                  {state.encounters.map((enc) => (
                    <div key={enc.id} style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <div style={{ fontWeight: 600, color: 'var(--bloom)' }}>{enc.title}</div>
                      <p className="scene-sub">{enc.description}</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
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
                </section>
              )}

              {/* Local Merchant */}
              {state.merchant && (
                <section className="card">
                  <div className="section-label">Market · {state.merchant.name}</div>
                  <div className="npc-grid">
                    {state.merchant.items.map((item) => (
                      <div key={item.id} className="card" style={{ padding: 10 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                          <strong>{item.name}</strong>
                          <span style={{ color: 'var(--star)' }}>◈ {item.value_echoes}</span>
                        </div>
                        <p className="scene-sub" style={{ marginBottom: 8 }}>{item.prism_description}</p>
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
                </section>
              )}
            </>
          )}

          {tab === 'map' && (
            <section className="card">
              <div className="section-label">World Map · Regions, Towns, Cities & Districts</div>
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
                        stroke="rgba(168, 85, 247, 0.35)"
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

              <div className="npc-grid" style={{ marginTop: 12 }}>
                {world.locations.map((loc) => (
                  <div key={loc.id} className="card" style={{ padding: 10 }}>
                    <div style={{ fontWeight: 600 }}>{loc.name}</div>
                    <div style={{ fontSize: 11, color: 'var(--quasar-bright)' }}>{loc.settlement_name}</div>
                    <div className="scene-sub" style={{ margin: '6px 0' }}>
                      {loc.unlocked ? loc.surface_description : loc.lock_reason}
                    </div>
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
            </section>
          )}

          {tab === 'quests' && (
            <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="section-label">Quest Journal</div>
              {state.quests.map((q) => (
                <div key={q.id} className="card" style={{ padding: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <strong style={{ color: q.status === 'completed' ? 'var(--emerald)' : 'var(--bloom)' }}>
                      {q.title}
                    </strong>
                    <span className="pill">{q.arc} · {q.status}</span>
                  </div>
                  <p className="scene-sub" style={{ margin: '6px 0' }}>{q.summary}</p>
                  <div style={{ fontSize: 12, color: 'var(--quasar-bright)' }}>
                    Objective: {q.current_objective}
                  </div>
                </div>
              ))}
            </section>
          )}

          {tab === 'inventory' && (
            <section className="card">
              <div className="section-label">Inventory & Symbolic Objects</div>
              <div className="npc-grid">
                {state.inventory.map((item) => (
                  <div key={item.id} className="card" style={{ padding: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{item.name} ×{item.quantity}</strong>
                      <span style={{ fontSize: 11, color: 'var(--star)' }}>{item.rarity}</span>
                    </div>
                    <p className="scene-sub" style={{ margin: '6px 0' }}>{item.active_description}</p>
                    <button
                      type="button"
                      className="btn btn-quasar"
                      disabled={busy}
                      onClick={() => handleUseItem(item.id)}
                    >
                      {item.equippable ? (item.equipped ? 'Unequip' : 'Equip') : 'Use'}
                    </button>
                  </div>
                ))}
              </div>
            </section>
          )}

          {tab === 'codex' && (
            <section className="card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div className="section-label">Lore Codex · Canon & Metaphysics</div>
              {codex.length === 0 ? (
                <p className="scene-sub">Loading canonical codex entries…</p>
              ) : (
                codex.map((entry) => (
                  <div key={entry.id} className="card" style={{ padding: 12 }}>
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
                ))
              )}
            </section>
          )}

          {tab === 'character' && (
            <>
              <section className="card">
                <div className="section-label">Psychometric Attributes</div>
                <div className="npc-grid">
                  {(['clarity', 'empathy', 'resolve', 'perception', 'veil_attunement'] as const).map((k) => (
                    <div key={k} className="card" style={{ padding: 10 }}>
                      <div className="section-label" style={{ marginBottom: 4 }}>{k.replace('_', ' ')}</div>
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
              </section>

              <section className="card">
                <div className="section-label">Factions</div>
                <div className="npc-grid">
                  {state.factions.map((f) => (
                    <div key={f.id} className="card" style={{ padding: 10 }}>
                      <strong>{f.name}</strong>
                      <div style={{ fontSize: 11, color: 'var(--quasar-bright)' }}>
                        {f.rank} ({f.reputation})
                      </div>
                      <p className="scene-sub" style={{ marginTop: 4 }}>{f.description}</p>
                    </div>
                  ))}
                </div>
              </section>

              {state.ending_status && (
                <section className="card">
                  <div className="section-label">Veil Convergence · Ending Trajectory</div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <strong style={{ color: state.ending_status.trajectory === 'true_ending_ready' ? 'var(--emerald)' : 'var(--bloom)' }}>
                      {state.ending_status.trajectory.replace(/_/g, ' ').toUpperCase()}
                    </strong>
                    <span className="pill">Max Sister Trust: {state.ending_status.max_sister_trust}</span>
                  </div>
                  <p className="scene-sub" style={{ marginBottom: 8 }}>{state.ending_status.summary}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {Object.entries(state.ending_status.criteria).map(([key, met]) => (
                      <span
                        key={key}
                        className="pill"
                        style={{ borderColor: met ? 'var(--emerald)' : 'var(--glass-border)', color: met ? 'var(--emerald)' : 'var(--text-dim)' }}
                      >
                        {met ? '✓' : '○'} {key.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </section>
              )}

              {shelf.length > 0 && (
                <section className="card">
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
                </section>
              )}

              <section className="card">
                <div className="section-label">Save Slots</div>
                {state.saves.length === 0 ? (
                  <p className="scene-sub">No saved checkpoints yet. Click "Save Checkpoint" in the left rail.</p>
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
              </section>
            </>
          )}
        </main>

        {/* Right Chronicle Rail */}
        <aside className="card">
          <div className="section-label">Chronicle & Memory</div>
          <div className="log-list">
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
        </aside>
      </div>

      {toast && <div className="toast">{toast}</div>}
    </div>
  )
}
