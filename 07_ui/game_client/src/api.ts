import type { GameState } from './types'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json() as Promise<T>
}

export const api = {
  getState: () => request<GameState>('/api/game/state'),
  travel: (location_id: string) =>
    request<{ ok: boolean; message: string; state: GameState }>('/api/world/travel', {
      method: 'POST',
      body: JSON.stringify({ location_id }),
    }),
  advanceVeil: () =>
    request<{ ok: boolean; veil_state: string; state: GameState }>('/api/world/advance-veil', {
      method: 'POST',
    }),
  talk: (npc_id: string, message: string) =>
    request<{ ok: boolean; speaker: string; reply: string; resonance_delta: number; state: GameState }>(
      '/api/dialogue/turn',
      { method: 'POST', body: JSON.stringify({ npc_id, message }) },
    ),
  buyItem: (item_id: string) =>
    request<{ ok: boolean; message: string; state: GameState }>('/api/economy/buy', {
      method: 'POST',
      body: JSON.stringify({ item_id }),
    }),
  useItem: (item_id: string) =>
    request<{ ok: boolean; message: string; state: GameState }>('/api/inventory/use', {
      method: 'POST',
      body: JSON.stringify({ item_id }),
    }),
  resolveEncounter: (encounter_id: string, choice_id: string) =>
    request<{
      ok: boolean
      success: boolean
      roll: number
      modifier: number
      total: number
      dc: number
      outcome_text: string
      state: GameState
    }>('/api/encounters/resolve', {
      method: 'POST',
      body: JSON.stringify({ encounter_id, choice_id }),
    }),
  saveGame: (slot_id: string, label: string) =>
    request<{ ok: boolean; label: string }>('/api/saves/save', {
      method: 'POST',
      body: JSON.stringify({ slot_id, label }),
    }),
  loadGame: (slot_id: string) =>
    request<{ ok: boolean; message: string; state: GameState }>(`/api/saves/load/${slot_id}`, {
      method: 'POST',
    }),
}
