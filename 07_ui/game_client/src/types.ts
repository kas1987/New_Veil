export interface LocationNode {
  id: string
  settlement_id: string
  settlement_name: string
  settlement_type: string
  district_id: string
  name: string
  type: string
  map_coords: { x: number; y: number }
  surface_description: string
  depth_description: string
  npcs: string[]
  objects: string[]
  services: string[]
  hidden: boolean
  unlocked: boolean
  lock_reason: string
  is_current: boolean
  is_adjacent: boolean
  discovered: boolean
}

export interface NpcProfile {
  id: string
  display_name: string
  category: string
  faction_id: string
  role: string
  surface_function: string
  hidden_function: string
  accent: string
  greeting: string
  portrait_url: string
  is_merchant: boolean
  can_join_party?: boolean
  in_party?: boolean
  bond?: number
  stance?: string
  relationship: {
    trust: number
    affection: number
    suspicion: number
    resistance: number
    interactions: number
  }
}

export interface InventoryItem {
  id: string
  name: string
  category: string
  rarity: string
  value_echoes: number
  equippable: boolean
  equipped: boolean
  quantity: number
  active_description: string
  stat_bonuses?: Record<string, number>
}

export interface QuestEntry {
  id: string
  title: string
  arc: string
  summary: string
  status: string
  stage_index: number
  current_objective: string
  stages: { index: number; objective: string; hint: string }[]
}

export interface FactionEntry {
  id: string
  name: string
  alignment: string
  description: string
  reputation: number
  rank: string
}

export interface EncounterEntry {
  id: string
  title: string
  description: string
  choices: {
    id: string
    label: string
    attribute: string
    dc: number
  }[]
}

export interface MerchantEntry {
  id: string
  name: string
  items: {
    id: string
    name: string
    value_echoes: number
    prism_description: string
    rarity: string
  }[]
}

export interface GameState {
  world: {
    world_id: string
    display_name: string
    day_count: number
    time_of_day: string
    veil_state: string
    echoes: number
    current_region: { id: string; name: string; description: string }
    current_settlement: { id: string; name: string; type: string }
    current_location: LocationNode
    active_party?: string[]
    locations: LocationNode[]
    connections: { from: string; to: string; bidirectional?: boolean }[]
  }
  player: {
    level: number
    xp: number
    resonance: number
    clarity: number
    empathy: number
    resolve: number
    perception: number
    veil_attunement: number
    turns_taken: number
    bonuses: Record<string, number>
    resonance_tier: { tier: number; name: string; description: string }
  }
  npcs_here: NpcProfile[]
  inventory: InventoryItem[]
  quests: QuestEntry[]
  factions: FactionEntry[]
  encounters: EncounterEntry[]
  merchant: MerchantEntry | null
  recent_logs: { id: number; agent_id: string; content: string; created_at: string }[]
  ending_status?: {
    trajectory: string
    summary: string
    criteria: Record<string, boolean>
    hidden_paths_found: string[]
    max_sister_trust: number
  }
  saves: { slot_id: string; label: string; updated_at: string }[]
}

export interface CodexEntry {
  id: string
  title: string
  category: string
  min_resonance: number
  unlocked: boolean
  excerpt: string
}

export interface ShelfCharacter {
  id: string
  display_name: string
  source: string
  portrait_url: string
}
