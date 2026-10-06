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
