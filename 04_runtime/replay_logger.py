"""Replay logger — deterministic event logging for audit and replay."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


class ReplayLogger:
    """Logs events to JSONL for deterministic replay and audit."""

    def __init__(self, log_path: str = "06_logs/replay.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, event: dict) -> None:
        """Log a single event with timestamp."""
        if "timestamp" not in event:
            event["timestamp"] = datetime.now(UTC).isoformat()
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_tick(self, tick: int, passed: list[dict], quarantined: list[dict]) -> None:
        """Log a complete tick result."""
        self.log_event({
            "type": "tick",
            "tick": tick,
            "passed_actions": passed,
            "quarantined_actions": quarantined,
            "passed_count": len(passed),
            "quarantined_count": len(quarantined),
        })

    def log_agent_action(self, agent_id: str, action: str, output: str,
                         alignment: dict, veil_state: str = "",
                         canon_refs: list | None = None) -> None:
        """Log an agent action with alignment scoring."""
        self.log_event({
            "type": "agent_action",
            "agent": agent_id,
            "action": action,
            "output": output,
            "alignment": alignment,
            "veil_state": veil_state,
            "canon_refs": canon_refs or [],
        })

    def log_memory_write(self, scope: str, content: str, agent_id: str = "",
                         emotional_tags: list | None = None,
                         canon_refs: list | None = None) -> None:
        """Log a memory write event."""
        self.log_event({
            "type": "memory_write",
            "scope": scope,
            "agent_id": agent_id,
            "content_snippet": content[:200],
            "emotional_tags": emotional_tags or [],
            "canon_refs": canon_refs or [],
        })

    def log_quarantine(self, agent_id: str, content: str, reason: str,
                       alignment: dict, veil_state: str = "") -> None:
        """Log a quarantine event."""
        self.log_event({
            "type": "quarantine",
            "agent_id": agent_id,
            "content_snippet": content[:200],
            "reason": reason,
            "alignment": alignment,
            "veil_state": veil_state,
        })

    def log_veil_state_change(self, from_state: str, to_state: str, tick: int) -> None:
        """Log a Veil state machine transition."""
        self.log_event({
            "type": "veil_state_change",
            "from": from_state,
            "to": to_state,
            "tick": tick,
        })

    def read_logs(self, limit: int = 100, event_type: str | None = None) -> list[dict]:
        """Read recent logs, optionally filtered by type."""
        if not self.log_path.exists():
            return []
        events = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event_type is None or event.get("type") == event_type:
                        events.append(event)
                except json.JSONDecodeError:
                    continue
        return events[-limit:]

    def get_stats(self) -> dict:
        """Get basic statistics about logged events."""
        if not self.log_path.exists():
            return {"total_events": 0}
        events = []
        with self.log_path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    events.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
        types = {}
        for e in events:
            t = e.get("type", "unknown")
            types[t] = types.get(t, 0) + 1
        return {
            "total_events": len(events),
            "by_type": types,
            "first_timestamp": events[0].get("timestamp") if events else None,
            "last_timestamp": events[-1].get("timestamp") if events else None,
        }
