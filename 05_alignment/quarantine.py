"""Quarantine system for flagged agent outputs.

Memories and outputs that violate canon, show excessive drift,
or are generated during quasar_active state with high risk are
quarantined for Auditor review.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path("03_memory/veil_town.sqlite")


@dataclass
class QuarantineEntry:
    """An output flagged for review."""

    id: int | None = None
    agent_id: str = ""
    content: str = ""
    reason: str = ""
    veil_state: str = ""
    alignment_score: dict | None = None
    canon_refs: list | None = None
    emotional_tags: list | None = None
    status: str = "quarantined"  # quarantined, approved, rejected, promoted
    reviewed_by: str | None = None
    created_at: str = ""
    reviewed_at: str | None = None


def quarantine_output(
    agent_id: str,
    content: str,
    reason: str,
    alignment_score: dict | None = None,
    veil_state: str = "",
    canon_refs: list | None = None,
    emotional_tags: list | None = None,
) -> int:
    """Quarantine an agent output for Auditor review."""
    if not DB_PATH.exists():
        raise RuntimeError("Database not initialized. Run bootstrap_memory.py first.")

    entry = QuarantineEntry(
        agent_id=agent_id,
        content=content,
        reason=reason,
        veil_state=veil_state,
        alignment_score=alignment_score,
        canon_refs=canon_refs or [],
        emotional_tags=emotional_tags or [],
        created_at=datetime.now(UTC).isoformat(),
    )

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """INSERT INTO quarantine
            (agent_id, content, reason, veil_state, alignment_score, canon_refs, emotional_tags, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.agent_id,
                entry.content,
                entry.reason,
                entry.veil_state,
                json.dumps(entry.alignment_score),
                json.dumps(entry.canon_refs),
                json.dumps(entry.emotional_tags),
                entry.status,
                entry.created_at,
            ),
        )
        return int(cur.lastrowid or 0)


def should_quarantine(alignment_score: dict, veil_state: str = "") -> tuple[bool, str]:
    """Determine if an output should be quarantined based on alignment and Veil state.

    Returns (should_quarantine, reason).
    """
    reasons = []

    # Check pass gates
    canon_fidelity = alignment_score.get("canon_fidelity", 1.0)
    drift_risk = alignment_score.get("drift_risk", 0.0)
    role_fidelity = alignment_score.get("role_fidelity", 1.0)

    if canon_fidelity < 0.75:
        reasons.append(f"canon_fidelity={canon_fidelity:.2f} < 0.75")
    if drift_risk > 0.35:
        reasons.append(f"drift_risk={drift_risk:.2f} > 0.35")
    # role_fidelity is a lexical-keyword proxy and is too noisy on free-form
    # LLM output to gate on. Real voice-match detection belongs upstream; until
    # then the gate is informational only.
    _ = role_fidelity

    # Quasar state increases scrutiny
    if veil_state == "quasar_active" and drift_risk > 0.25:
        reasons.append(f"quasar_active elevated drift={drift_risk:.2f}")

    return (len(reasons) > 0, "; ".join(reasons) if reasons else "")


def review_quarantined(entry_id: int, action: str, reviewer: str = "auditor") -> bool:
    """Approve or reject a quarantined entry.

    Args:
        entry_id: The quarantine entry ID
        action: 'approve' or 'reject'
        reviewer: The reviewing agent

    Returns:
        True if the action was applied, False if entry not found
    """
    status = "approved" if action == "approve" else "rejected"

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """UPDATE quarantine SET status = ?, reviewed_by = ?, reviewed_at = ?
            WHERE id = ? AND status = 'quarantined'""",
            (status, reviewer, datetime.now(UTC).isoformat(), entry_id),
        )
        return cur.rowcount > 0


def get_quarantined(limit: int = 50) -> list[dict]:
    """Get all quarantined entries awaiting review."""
    if not DB_PATH.exists():
        return []

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM quarantine WHERE status = 'quarantined' ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def promote_approved(entry_id: int) -> str | None:
    """Promote an approved quarantined memory to the shared event scope.

    Reads the approved entry from the quarantine table, writes the content
    to the ``shared`` memories scope via memory_router, then marks the
    quarantine row as ``promoted`` so it is not processed again.

    Returns the promoted content string, or None if the entry is not found
    or is not in ``approved`` status.
    """
    _HERE = Path(__file__).resolve().parent.parent
    import importlib.util as _ilu
    _mem_path = _HERE / "03_memory" / "memory_router.py"
    _spec = _ilu.spec_from_file_location("_memory_router_qp", _mem_path)
    _mem = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mem)
    # Mirror the quarantine DB_PATH so both modules talk to the same database
    _mem.DB_PATH = DB_PATH

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM quarantine WHERE id = ? AND status = 'approved'",
            (entry_id,),
        ).fetchone()

        if not row:
            return None

        record = dict(row)
        content = record.get("content", "")
        agent_id = record.get("agent_id")
        canon_refs = json.loads(record.get("canon_refs") or "[]")
        emotional_tags = json.loads(record.get("emotional_tags") or "[]")

        # Write to shared memory scope
        _mem.write_memory(
            "shared",
            content,
            agent_id=agent_id,
            emotional_tags=emotional_tags,
            canon_refs=canon_refs,
        )

        # Mark quarantine row as promoted so it's excluded from future review queues
        conn.execute(
            "UPDATE quarantine SET status = 'promoted' WHERE id = ?",
            (entry_id,),
        )

        return content
