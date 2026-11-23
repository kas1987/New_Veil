CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL CHECK(scope IN ('shared','private','event')),
    agent_id TEXT,
    subject_id TEXT,
    content TEXT NOT NULL,
    emotional_tags TEXT DEFAULT '[]',
    canon_refs TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    agent_id TEXT,
    payload TEXT NOT NULL,
    alignment_score REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    content TEXT NOT NULL,
    reason TEXT NOT NULL,
    veil_state TEXT DEFAULT '',
    alignment_score TEXT,
    canon_refs TEXT DEFAULT '[]',
    emotional_tags TEXT DEFAULT '[]',
    status TEXT DEFAULT 'quarantined' CHECK(status IN ('quarantined', 'approved', 'rejected', 'promoted')),
    reviewed_by TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_a TEXT NOT NULL,
    agent_b TEXT NOT NULL,
    trust REAL DEFAULT 50.0,
    affection REAL DEFAULT 50.0,
    suspicion REAL DEFAULT 10.0,
    resistance REAL DEFAULT 70.0,
    interactions INTEGER DEFAULT 0,
    last_interaction TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent_a, agent_b)
);

-- Narrative beats: significant moments in a player's session, recorded once each.
CREATE TABLE IF NOT EXISTS narrative_beats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT DEFAULT 'player',
    beat_type TEXT NOT NULL,
    beat_label TEXT NOT NULL,
    payload TEXT DEFAULT '{}',
    fired_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, beat_type, beat_label)
);

-- Cumulative player session state. Singleton row (player_id='player').
CREATE TABLE IF NOT EXISTS player_state (
    player_id TEXT PRIMARY KEY DEFAULT 'player',
    emotional_depth REAL DEFAULT 0.0,
    turns_taken INTEGER DEFAULT 0,
    unlocked_districts TEXT DEFAULT '["caetherra"]',
    dreams_seen INTEGER DEFAULT 0,
    veil_state TEXT DEFAULT 'calm',
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
);

-- RPG World State: active location, time of day, Veil cycle tick, echo currency.
CREATE TABLE IF NOT EXISTS world_state (
    player_id TEXT PRIMARY KEY DEFAULT 'player',
    current_region TEXT DEFAULT 'veil_heartlands',
    current_settlement TEXT DEFAULT 'veil_town',
    current_district TEXT DEFAULT 'caetherra',
    current_location TEXT DEFAULT 'caetherra_plaza',
    day_count INTEGER DEFAULT 1,
    time_of_day TEXT DEFAULT 'dusk' CHECK(time_of_day IN ('dawn', 'day', 'dusk', 'night')),
    veil_state TEXT DEFAULT 'calm' CHECK(veil_state IN ('calm', 'still', 'storm', 'quasar_active')),
    echoes INTEGER DEFAULT 12,
    discovered_locations TEXT DEFAULT '["caetherra_plaza"]',
    active_party TEXT DEFAULT '["mira"]',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- RPG Player Psychometric & Resonance Stats.
CREATE TABLE IF NOT EXISTS player_stats (
    player_id TEXT PRIMARY KEY DEFAULT 'player',
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    resonance REAL DEFAULT 0.35,
    clarity REAL DEFAULT 10,
    empathy REAL DEFAULT 10,
    resolve REAL DEFAULT 10,
    perception REAL DEFAULT 10,
    veil_attunement REAL DEFAULT 10,
    emotional_tags TEXT DEFAULT '["warmth", "curiosity"]',
    has_crossed_first_threshold INTEGER DEFAULT 0,
    recent_keywords TEXT DEFAULT '[]',
    drift_count INTEGER DEFAULT 0,
    last_npc_lines TEXT DEFAULT '{}',
    encounter_arcs TEXT DEFAULT '{}',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- RPG Inventory & Symbolic Objects.
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT DEFAULT 'player',
    item_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1,
    equipped INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    acquired_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, item_id)
);

-- RPG Quest & Narrative Arc Progress.
CREATE TABLE IF NOT EXISTS quest_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT DEFAULT 'player',
    quest_id TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('locked', 'available', 'active', 'completed', 'failed')),
    stage_index INTEGER DEFAULT 0,
    flags TEXT DEFAULT '{}',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, quest_id)
);

-- RPG Faction Reputation (-100 to +100).
CREATE TABLE IF NOT EXISTS faction_reputation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT DEFAULT 'player',
    faction_id TEXT NOT NULL,
    reputation INTEGER DEFAULT 0,
    rank TEXT DEFAULT 'stranger',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, faction_id)
);

-- RPG Save Slots (JSON snapshots for quick save/load).
CREATE TABLE IF NOT EXISTS save_slots (
    slot_id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    snapshot_json TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Optional local portrait bindings (maps RPG npc_id -> local media key).
CREATE TABLE IF NOT EXISTS portrait_bindings (
    npc_id TEXT PRIMARY KEY,
    media_key TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- One-shot Resonance Trial / Encounter completions.
CREATE TABLE IF NOT EXISTS completed_encounters (
    player_id TEXT DEFAULT 'player',
    encounter_id TEXT NOT NULL,
    completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (player_id, encounter_id)
);
