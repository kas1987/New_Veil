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
    active_party: ['mira'],
    locations: [],
    connections: [],
  },
  player: {
    level: 1,
    xp: 0,
    resonance: 350.0,
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
      can_join_party: true,
      in_party: true,
      bond: 12.0,
      bond_tier: 'stranger',
      stance: 'open',
      relationship: { trust: 52, affection: 50, suspicion: 10, resistance: 65, interactions: 0 },
    },
  ],
  objects_here: [
    {
      id: 'lantern',
      display_name: 'Lantern',
      inspected_prism: false,
      inspected_dq: false,
      can_reveal_dq: false,
      active_description: 'A warm lantern lights the path.',
    },
  ],
  narrative_beats: [],
  district_status: {
    district_id: 'caetherra',
    false_comfort_available: false,
    false_comfort_state: 'unanswered',
    unseen_gate_discovered: false,
    caetherra_awakened: false,
  },
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
  ending_status: {
    trajectory: 'false_ending_risk',
    summary: 'You still walk the warm Prism surface.',
    criteria: { resonance_gt_80: false, hidden_path_unlocked: false },
    hidden_paths_found: [],
    max_sister_trust: 52,
  },
  saves: [],
}

describe('The Veil RPG Client', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => {
        if (url === '/api/codex') {
          return {
            ok: true,
            json: async () => ({
              entries: [
                {
                  id: 'lore_bible',
                  title: 'Veil Town Lore Bible',
                  category: 'Canon',
                  min_resonance: 0,
                  unlocked: true,
                  excerpt: 'Veil Town exists behind the Veil.',
                },
              ],
            }),
          }
        }
        if (url === '/api/media/local-shelf') {
          return { ok: true, json: async () => ({ characters: [] }) }
        }
        if (url === '/api/dialogue/turn') {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              speaker: 'Mira',
              reply: 'Listen closely to the Prism.',
              resonance_delta: 2.0,
              state: MOCK_STATE,
            }),
          }
        }
        if (url === '/api/world/advance-veil') {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              veil_state: 'still',
              state: { ...MOCK_STATE, world: { ...MOCK_STATE.world, veil_state: 'still' } },
            }),
          }
        }
        if (url === '/api/world/inspect') {
          return {
            ok: true,
            json: async () => ({
              ok: true,
              message: 'A warm lantern lights the path.',
              state: {
                ...MOCK_STATE,
                objects_here: [
                  {
                    ...MOCK_STATE.objects_here![0],
                    inspected_prism: true,
                  },
                ],
              },
            }),
          }
        }
        return { ok: true, json: async () => MOCK_STATE }
      }),
    )
  })

  it('renders full-bleed stage, dialogue dock, Veil shift, hotkeys, and slide-over drawers', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Caetherra Sunlit Plaza')).toBeTruthy()
    })

    expect(screen.getAllByText('Mira').length).toBeGreaterThan(0)
    expect(screen.getByText(/First Light/i)).toBeTruthy()
    expect(screen.getByText('350.0')).toBeTruthy()
    expect(screen.getByText(/Bond/i)).toBeTruthy()

    // Send quick dialogue prompt
    fireEvent.click(screen.getByRole('button', { name: /Ask about the Veil/i }))
    await waitFor(() => {
      expect(screen.getByText(/Listen closely to the Prism/i)).toBeTruthy()
    })

    // Inspect symbolic object
    fireEvent.click(screen.getByRole('button', { name: /Inspect: Lantern/i }))
    await waitFor(() => {
      expect(screen.getByText('A warm lantern lights the path.')).toBeTruthy()
    })

    // Toggle Diegetic mode: hides numeric 350.0 & Bond 12 while keeping qualitative cues
    fireEvent.click(screen.getByRole('button', { name: /Numeric/i }))
    expect(screen.queryByText('350.0')).toBeNull()
    expect(screen.getByText('stranger')).toBeTruthy()
    expect(screen.getByText(/First Light/i)).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: /Diegetic/i }))
    expect(screen.getByText('350.0')).toBeTruthy()

    // Shift Veil state
    fireEvent.click(screen.getByRole('button', { name: /Veil:/i }))
    await waitFor(() => {
      expect(screen.getByText('Veil shifted to still')).toBeTruthy()
    })

    // Open Lore Codex drawer via hotkey 'c'
    fireEvent.keyDown(window, { key: 'c' })
    await waitFor(() => {
      expect(screen.getByText('Veil Town Lore Bible')).toBeTruthy()
    })

    // Close drawer via Escape
    fireEvent.keyDown(window, { key: 'Escape' })
    expect(screen.queryByText('Veil Town Lore Bible')).toBeNull()

    // Open Quest Journal drawer via ghost rail button
    fireEvent.click(screen.getByRole('button', { name: /Quest Journal/i }))
    expect(screen.getByText('The First Light')).toBeTruthy()

    // Open Relics & Pack drawer
    fireEvent.click(screen.getByRole('button', { name: /Relics & Pack/i }))
    expect(screen.getByText(/Crystallized Echo Shard/i)).toBeTruthy()

    // Open Stats & Factions drawer (verify Ending Trajectory card)
    fireEvent.click(screen.getByRole('button', { name: /Stats & Factions/i }))
    expect(screen.getByText('The Nine Sisters')).toBeTruthy()
    expect(screen.getByText(/FALSE ENDING RISK/i)).toBeTruthy()
  })
})
