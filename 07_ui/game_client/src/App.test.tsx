import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'
import type { GameState } from './types'

const MOCK_STATE: GameState = {
  world: {
    world_id: 'the_veil',
    display_name: 'The Veil',
    day_count: 1,
    time_of_day: 'dusk',
    veil_state: 'calm',
    echoes: 12,
    current_region: { id: 'veil_heartlands', name: 'The Veil Heartlands', description: 'Core' },
    current_settlement: { id: 'veil_town', name: 'Veil Town (Caetherra)', type: 'city' },
    current_location: {
      id: 'caetherra_plaza',
      settlement_id: 'veil_town',
      settlement_name: 'Veil Town (Caetherra)',
      settlement_type: 'city',
      district_id: 'caetherra',
      name: 'Caetherra Sunlit Plaza',
      type: 'plaza',
      map_coords: { x: 48, y: 54 },
      surface_description: 'Warm limestone arches and amber lanterns.',
      depth_description: 'Shadows linger too long.',
      npcs: ['mira'],
      objects: ['lantern'],
      services: ['rest'],
      hidden: false,
      unlocked: true,
      lock_reason: '',
      is_current: true,
      is_adjacent: false,
      discovered: true,
    },
    locations: [],
    connections: [],
  },
  player: {
    level: 1,
    xp: 0,
    resonance: 0.35,
    clarity: 10,
    empathy: 10,
    resolve: 10,
    perception: 10,
    veil_attunement: 10,
    turns_taken: 0,
    bonuses: {},
    resonance_tier: { tier: 2, name: 'First Light', description: 'Sees thresholds.' },
  },
  npcs_here: [
    {
      id: 'mira',
      display_name: 'Mira',
      category: 'sister',
      faction_id: 'nine_sisters',
      role: 'First Awakening Guide',
      surface_function: 'Welcome guide',
      hidden_function: 'Filter for depth',
      accent: '#e879f9',
      greeting: 'The lanterns burn brighter tonight.',
      portrait_url: '/api/media/portrait/mira',
      is_merchant: false,
      relationship: { trust: 52, affection: 50, suspicion: 10, resistance: 65, interactions: 0 },
    },
  ],
  inventory: [
    {
      id: 'echo_shard',
      name: 'Crystallized Echo Shard',
      category: 'consumable',
      rarity: 'common',
      value_echoes: 5,
      equippable: false,
      equipped: false,
      quantity: 2,
      active_description: 'A humming glass sliver.',
    },
  ],
  quests: [
    {
      id: 'q_first_awakening',
      title: 'The First Light',
      arc: 'main',
      summary: 'Meet Mira in Caetherra.',
      status: 'active',
      stage_index: 0,
      current_objective: 'Speak with Mira in Caetherra Sunlit Plaza.',
      stages: [{ index: 0, objective: 'Speak with Mira in Caetherra Sunlit Plaza.', hint: 'Say hello' }],
    },
  ],
  factions: [
    {
      id: 'nine_sisters',
      name: 'The Nine Sisters',
      alignment: 'Veil Sovereign',
      description: 'Core archetypal forces.',
      reputation: 0,
      rank: 'Unnoticed',
    },
  ],
  encounters: [],
  merchant: null,
  recent_logs: [],
  saves: [],
}

describe('The Veil RPG Client', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => MOCK_STATE,
      }),
    )
  })

  it('renders HUD, current location, Mira, and switches RPG tabs cleanly', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Caetherra Sunlit Plaza')).toBeTruthy()
    })

    expect(screen.getByText('Mira')).toBeTruthy()
    expect(screen.getByText(/First Light/i)).toBeTruthy()

    // Switch to Quest Journal tab
    fireEvent.click(screen.getByRole('button', { name: /Quest Journal/i }))
    expect(screen.getByText('The First Light')).toBeTruthy()

    // Switch to Relics & Pack tab
    fireEvent.click(screen.getByRole('button', { name: /Relics & Pack/i }))
    expect(screen.getByText(/Crystallized Echo Shard/i)).toBeTruthy()

    // Switch to Stats & Factions tab
    fireEvent.click(screen.getByRole('button', { name: /Stats & Factions/i }))
    expect(screen.getByText('The Nine Sisters')).toBeTruthy()
  })
})

