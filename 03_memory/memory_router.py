"""Memory router — SQLite-backed memory with shared/private/event scopes."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

DB_PATH = Path("03_memory/veil_town.sqlite")
SCHEMA_PATH = Path("03_memory/schema.sql")


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def write_memory(
    scope: str,
    content: str,
    agent_id: str | None = None,
    emotional_tags=None,
    canon_refs=None,
) -> int:
    emotional_tags = emotional_tags or []
    canon_refs = canon_refs or []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            "INSERT INTO memories(scope, agent_id, content, emotional_tags, canon_refs) VALUES (?, ?, ?, ?, ?)",
            (
                scope,
                agent_id,
                content,
                json.dumps(emotional_tags),
                json.dumps(canon_refs),
            ),
        )
        return int(cur.lastrowid)


def read_recent_memories(limit: int = 10):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,)
            )
        ]


def read_quarantined(limit: int = 50):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM quarantine WHERE status = 'quarantined' ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
        ]


def _clamp_stock(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(x)))


def update_relationship(
    agent_a: str,
    agent_b: str,
    trust_delta: float = 0,
    affection_delta: float = 0,
    suspicion_delta: float = 0,
    resistance_delta: float = 0,
) -> dict:
    """Update or create a relationship between two agents.

    All four stocks (trust, affection, suspicion, resistance) are clamped to
    [0, 100] after the delta is applied. This matches the DSSM CoreState
    convention so the persisted state stays in the nominal range even across
    long sessions where deltas accumulate freely.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM relationships WHERE agent_a = ? AND agent_b = ?",
            (agent_a, agent_b),
        ).fetchone()

        if row:
            new_trust = _clamp_stock(row["trust"] + trust_delta)
            new_aff = _clamp_stock(row["affection"] + affection_delta)
            new_susp = _clamp_stock(row["suspicion"] + suspicion_delta)
            new_resist = _clamp_stock(row["resistance"] + resistance_delta)
            conn.execute(
                """UPDATE relationships SET trust = ?, affection = ?,
                suspicion = ?, resistance = ?,
                interactions = interactions + 1,
                updated_at = CURRENT_TIMESTAMP WHERE agent_a = ? AND agent_b = ?""",
                (new_trust, new_aff, new_susp, new_resist, agent_a, agent_b),
            )
        else:
            conn.execute(
                """INSERT INTO relationships (agent_a, agent_b, trust, affection, suspicion, resistance)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    agent_a,
                    agent_b,
                    _clamp_stock(50.0 + trust_delta),
                    _clamp_stock(50.0 + affection_delta),
                    _clamp_stock(10.0 + suspicion_delta),
                    _clamp_stock(70.0 + resistance_delta),
                ),
            )
        row = conn.execute(
            "SELECT * FROM relationships WHERE agent_a = ? AND agent_b = ?",
            (agent_a, agent_b),
        ).fetchone()
        return dict(row)


def read_player_state(player_id: str = "player") -> dict:
    """Return the current player state, creating a default row if absent."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM player_state WHERE player_id = ?", (player_id,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO player_state (player_id) VALUES (?)", (player_id,)
            )
            row = conn.execute(
                "SELECT * FROM player_state WHERE player_id = ?", (player_id,)
            ).fetchone()
        result = dict(row)
    if isinstance(result.get("unlocked_districts"), str):
        try:
            result["unlocked_districts"] = json.loads(result["unlocked_districts"])
        except (json.JSONDecodeError, TypeError):
            result["unlocked_districts"] = ["caetherra"]
    return result


def record_beat(
    beat_type: str,
    beat_label: str,
    payload: dict | None = None,
    player_id: str = "player",
) -> bool:
    """Record a narrative beat once per (player, type, label). Returns True if newly recorded."""
    payload_json = json.dumps(payload or {})
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute(
                "INSERT INTO narrative_beats (player_id, beat_type, beat_label, payload) "
                "VALUES (?, ?, ?, ?)",
                (player_id, beat_type, beat_label, payload_json),
            )
            return True
        except sqlite3.IntegrityError:
            return False  # Already recorded


def read_beats(player_id: str = "player", limit: int = 50) -> list[dict]:
    """Return narrative beats in chronological order (oldest first)."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM narrative_beats WHERE player_id = ? "
            "ORDER BY fired_at ASC LIMIT ?",
            (player_id, limit),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d.get("payload") or "{}")
            except (json.JSONDecodeError, TypeError):
                d["payload"] = {}
            result.append(d)
        return result


def update_player_state(
    player_id: str = "player",
    depth_delta: float = 0.0,
    dreams_seen_delta: int = 0,
    unlock_district: str | None = None,
    veil_state: str | None = None,
) -> dict:
    """Accumulate updates to the player session state."""
    current = read_player_state(player_id)
    new_depth = max(0.0, min(1.0, current["emotional_depth"] + depth_delta))
    new_turns = current["turns_taken"] + 1
    new_dreams = current["dreams_seen"] + dreams_seen_delta
    unlocked = list(current.get("unlocked_districts") or ["caetherra"])
    if unlock_district and unlock_district not in unlocked:
        unlocked.append(unlock_district)
    new_veil = veil_state if veil_state else current.get("veil_state", "calm")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """UPDATE player_state SET
                emotional_depth = ?,
                turns_taken = ?,
                dreams_seen = ?,
                unlocked_districts = ?,
                veil_state = ?,
                last_updated = CURRENT_TIMESTAMP
               WHERE player_id = ?""",
            (
                new_depth,
                new_turns,
                new_dreams,
                json.dumps(unlocked),
                new_veil,
                player_id,
            ),
        )
    return read_player_state(player_id)


if __name__ == "__main__":
    init_db()
    print("Veil memory initialized:", DB_PATH)
