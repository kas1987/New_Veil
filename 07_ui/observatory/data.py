"""Observatory data layer — all I/O, no Gradio imports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from veil_loader import load_module

_HERE = Path(__file__).resolve().parent  # 07_ui/observatory/
_ROOT = _HERE.parent.parent  # project root

_LOG_PATH = _ROOT / "06_logs" / "replay.jsonl"

_memory_router = load_module("memory_router", _ROOT / "03_memory" / "memory_router.py")
_quarantine_mod = load_module("quarantine", _ROOT / "05_alignment" / "quarantine.py")

_DISTRICTS_ALL = ["caetherra", "ashveil", "the_hollow"]


# ── replay log helpers ─────────────────────────────────────────────────────


def _iter_replay(log_path: Path | None = None) -> list[dict]:
    path = log_path or _LOG_PATH
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


# ── existing reads (backward-compatible for gradio_app.py) ────────────────


def read_replay(limit: int = 20) -> str:
    if not _LOG_PATH.exists():
        return "No replay logs yet."
    lines = _LOG_PATH.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[-limit:]) if lines else "No replay logs yet."


def read_relationships() -> list[list]:
    db = _memory_router.DB_PATH
    if not db.exists():
        return [["(no database — run bootstrap_memory.py)", "", "", "", "", ""]]
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT agent_a, agent_b, trust, affection, suspicion, interactions "
                "FROM relationships ORDER BY updated_at DESC"
            ).fetchall()
        except sqlite3.OperationalError:
            return [["(no relationships table yet)", "", "", "", "", ""]]
    if not rows:
        return [["(no relationships yet)", "", "", "", "", ""]]
    return [
        [
            r["agent_a"],
            r["agent_b"],
            f"{r['trust']:.1f}",
            f"{r['affection']:.1f}",
            f"{r['suspicion']:.1f}",
            r["interactions"],
        ]
        for r in rows
    ]


def read_relationships_chart_data() -> list[dict]:
    """Returns full relationship rows including resistance — used by radar chart."""
    db = _memory_router.DB_PATH
    if not db.exists():
        return []
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT agent_a, agent_b, trust, affection, suspicion, resistance "
                "FROM relationships ORDER BY updated_at DESC"
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [dict(r) for r in rows]


def read_agent_player_relationship(agent_id: str) -> dict:
    """Relationship telemetry for agent ↔ player dyad (PDR-0004)."""
    db = _memory_router.DB_PATH
    if not db.exists():
        return {}
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT agent_a, agent_b, trust, affection, suspicion, resistance, interactions "
                "FROM relationships "
                "WHERE (agent_a = ? AND agent_b = 'player') OR (agent_b = ? AND agent_a = 'player') "
                "ORDER BY updated_at DESC LIMIT 1",
                (agent_id, agent_id),
            ).fetchone()
        except sqlite3.OperationalError:
            return {}
    return dict(row) if row else {}


def read_quarantine() -> list[list]:
    try:
        rows = _memory_router.read_quarantined(50)
    except Exception as e:
        return [[f"(error: {e})", "", "", ""]]
    if not rows:
        return [["(no quarantined entries)", "", "", ""]]
    return [
        [
            r.get("id", ""),
            r.get("agent_id", ""),
            (r.get("reason", "") or "")[:80],
            (r.get("content", "") or "")[:100],
        ]
        for r in rows
    ]


def read_events(limit: int = 20) -> list[list]:
    _EVENT_TYPES = {"symbolic_event", "dream_generated", "agent_message", "echo_fired"}
    if not _LOG_PATH.exists():
        return [["(no replay log)", "", "", ""]]
    out = []
    for line in _LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        et = ev.get("type", ev.get("action", ""))
        if et in _EVENT_TYPES or "event_id" in ev:
            out.append(
                [
                    ev.get("timestamp", "")[:19],
                    et,
                    ev.get("agent_id", ev.get("agent", "")),
                    json.dumps(ev, ensure_ascii=False)[:200],
                ]
            )
    return (out[-limit:][::-1]) if out else [["(no symbolic events yet)", "", "", ""]]


def read_player_state() -> dict:
    try:
        return _memory_router.read_player_state("player")
    except Exception as e:
        return {"error": str(e)}


def read_beats() -> list[list]:
    try:
        beats = _memory_router.read_beats("player", limit=50)
    except Exception as e:
        return [[f"(error: {e})", "", "", ""]]
    if not beats:
        return [["(no beats recorded yet)", "", "", ""]]
    return [
        [
            b.get("fired_at", "")[:19],
            b.get("beat_type", ""),
            b.get("beat_label", ""),
            json.dumps(b.get("payload", {}), ensure_ascii=False)[:160],
        ]
        for b in beats
    ]


def read_queue_jsonl(path: Path, limit: int = 30) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out[-limit:][::-1]


# ── new reads ──────────────────────────────────────────────────────────────


def read_memories(
    agent_id: str | None = None,
    scope: str | None = None,
    limit: int = 50,
) -> list[list]:
    """Returns rows: [id, scope, agent_id, content (truncated 120), created_at]."""
    db = _memory_router.DB_PATH
    if not db.exists():
        return [["(no database)", "", "", "", ""]]
    query = "SELECT id, scope, agent_id, content, created_at FROM memories WHERE 1=1"
    params: list = []
    if agent_id:
        query += " AND agent_id = ?"
        params.append(agent_id)
    if scope:
        query += " AND scope = ?"
        params.append(scope)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(query, params).fetchall()
        except sqlite3.OperationalError:
            return [["(no memories table yet)", "", "", "", ""]]
    if not rows:
        return [["(no memories)", "", "", "", ""]]
    return [
        [
            r["id"],
            r["scope"],
            r["agent_id"] or "",
            (r["content"] or "")[:120],
            (r["created_at"] or "")[:19],
        ]
        for r in rows
    ]


def read_veil_series(limit: int = 200) -> list[dict]:
    """Returns [{turn_index, veil_state, accumulated_depth, timestamp}] for run_once events."""
    events = _iter_replay()
    out = []
    turn = 0
    for ev in events:
        if ev.get("action") != "run_once":
            continue
        out.append(
            {
                "turn_index": turn,
                "veil_state": ev.get("veil_state", "calm"),
                "accumulated_depth": ev.get("accumulated_depth", 0.0),
                "timestamp": ev.get("timestamp", ""),
            }
        )
        turn += 1
    return out[-limit:]


def read_alignment_series(limit: int = 200) -> list[dict]:
    """Returns [{timestamp, agent_id, prism_resonance, dark_quasar_resonance,
    emotional_depth, pass_gate}] for run_once events with dream_alignment."""
    events = _iter_replay()
    out = []
    for ev in events:
        if ev.get("action") != "run_once":
            continue
        da = ev.get("dream_alignment")
        if not da:
            continue
        out.append(
            {
                "timestamp": ev.get("timestamp", ""),
                "agent_id": ev.get("agent_id", "unknown"),
                "prism_resonance": da.get("prism_resonance", 0.0),
                "dark_quasar_resonance": da.get("dark_quasar_resonance", 0.0),
                "emotional_depth": da.get("emotional_depth", 0.0),
                "pass_gate": da.get("pass_gate", False),
            }
        )
    return out[-limit:]


def read_district_status() -> dict:
    """Returns {unlocked: [...], locked: [...]} using the canonical district list."""
    try:
        ps = _memory_router.read_player_state("player")
        unlocked = ps.get("unlocked_districts") or ["caetherra"]
    except Exception:
        unlocked = ["caetherra"]
    locked = [d for d in _DISTRICTS_ALL if d not in unlocked]
    return {"unlocked": list(unlocked), "locked": locked}


def approve_and_promote(entry_id: int) -> str:
    """Mark quarantine entry approved then promote to shared memory.
    Returns a human-readable status message."""
    try:
        approved = _quarantine_mod.review_quarantined(entry_id, "approve", "auditor")
        if not approved:
            return f"Entry {entry_id} not found or already reviewed."
        content = _quarantine_mod.promote_approved(entry_id)
        if content is None:
            return f"Entry {entry_id} approved but promotion returned None (check DB constraint)."
        return f"Entry {entry_id} approved and promoted to shared memory."
    except Exception as e:
        return f"Error processing entry {entry_id}: {e}"
