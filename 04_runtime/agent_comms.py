"""Veil Town Agent-to-Agent Communications Protocol.

P2.7: Veil-state distortion layer
----------------------------------
Messages sent between agents are distorted by the active Veil state and the
trust level of the dyad.

Distortion model (applied to content at send time):
  - calm / still  : no distortion if trust >= 50; minor echo fragmentation below that
  - storm         : moderate fragmentation regardless of trust; high trust reduces depth
  - quasar_active : heavy fragmentation + gravity echo appended; trust only slightly
                    attenuates the quasar gravity effect

Fragmentation: some sentences are replaced with "…" to simulate signal interference.
Gravity echo: a short dark postscript is appended at quasar_active.

The original content is preserved as ``original_content`` on the returned Message so
callers can log both the raw and distorted form.
"""

from __future__ import annotations

import json
import random
import sqlite3
import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

# Monotonic sequence counter — guards against same-microsecond timestamps
# when two sends happen back-to-back. Used in read_thread/read_inbox sort.
_seq_lock = threading.Lock()
_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    with _seq_lock:
        _seq_counter += 1
        return _seq_counter


@dataclass
class Message:
    msg_id: str
    from_agent: str
    to_agent: str
    content: str
    emotional_tone: str
    canon_refs: list[str]
    timestamp: str
    # P2.7: distortion metadata (None if no distortion was applied)
    original_content: str | None = None
    distortion_applied: str | None = None  # e.g. "storm_fragment", "quasar_gravity"


# ---------------------------------------------------------------------------
# P2.7 — Veil distortion helpers
# ---------------------------------------------------------------------------

_QUASAR_ECHOES = [
    "The gravity remembers.",
    "The Dark Quasar pulls at the edges of meaning.",
    "Something essential was lost in transit.",
    "The Veil distorts what it cannot contain.",
    "Signal integrity: compromised.",
]

_RNG = random.Random()  # Seeded per-call for determinism in tests via monkeypatch


def _fragment_sentences(text: str, drop_rate: float) -> str:
    """Replace sentences with '…' at the given drop_rate (0–1)."""
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    result = []
    for sent in sentences:
        if _RNG.random() < drop_rate:
            result.append("…")
        else:
            result.append(sent)
    return " ".join(result)


def _apply_distortion(
    content: str,
    veil_state: str,
    trust: float,
) -> tuple[str, str | None]:
    """Return (distorted_content, distortion_label | None).

    trust is 0–100; higher trust reduces fragmentation in calm/still/storm.
    quasar_active always adds gravity echo; trust slightly reduces fragment rate.
    """
    if veil_state in ("calm", "still"):
        # Low trust adds minor echoes; high trust → no distortion
        if trust >= 50.0:
            return content, None
        drop_rate = 0.10 * (1.0 - trust / 50.0)  # max 10% at trust=0
        distorted = _fragment_sentences(content, drop_rate)
        return distorted, "echo_fragment"

    if veil_state == "storm":
        # Base 20% fragment rate; trust (0–100) reduces by up to 15%
        drop_rate = max(0.05, 0.20 - 0.15 * (trust / 100.0))
        distorted = _fragment_sentences(content, drop_rate)
        return distorted, "storm_fragment"

    if veil_state == "quasar_active":
        # Heavy fragmentation (25–40%); trust reduces by up to 15%
        drop_rate = max(0.10, 0.40 - 0.15 * (trust / 100.0))
        distorted = _fragment_sentences(content, drop_rate)
        echo = _RNG.choice(_QUASAR_ECHOES)
        distorted = f"{distorted} [{echo}]"
        return distorted, "quasar_gravity"

    return content, None


class AgentComms:
    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent
        self.project_root = project_root
        self.events_dir = project_root / "03_memory" / "events"
        self.log_path = project_root / "06_logs" / "replay.jsonl"
        self.agents_dirs: list[Path] = [
            project_root / "02_agents",
            project_root / "13_agents",
        ]

    @property
    def index_path(self) -> Path:
        return self.events_dir / "index.jsonl"

    def _lookup_trust(self, agent_a: str, agent_b: str) -> float:
        """Return trust value for the dyad, defaulting to 35.0 if not found."""
        db = self.project_root / "03_memory" / "veil_town.sqlite"
        if not db.exists():
            return 35.0
        try:
            with sqlite3.connect(db) as conn:
                row = conn.execute(
                    "SELECT trust FROM relationships WHERE agent_a = ? AND agent_b = ?",
                    (agent_a, agent_b),
                ).fetchone()
                if row:
                    return float(row[0])
                # Try reversed dyad
                row = conn.execute(
                    "SELECT trust FROM relationships WHERE agent_a = ? AND agent_b = ?",
                    (agent_b, agent_a),
                ).fetchone()
                return float(row[0]) if row else 35.0
        except Exception:
            return 35.0

    def _agent_exists(self, agent_id: str) -> bool:
        if agent_id == "player":
            return True
        for agents_dir in self.agents_dirs:
            if not agents_dir.exists():
                continue
            # Direct child
            for candidate in agents_dir.iterdir():
                if candidate.is_dir() and candidate.name == agent_id:
                    return True
            # Nested groups (e.g., 13_agents/sisters/solenne)
            for group in agents_dir.iterdir():
                if group.is_dir():
                    hit = group / agent_id
                    if hit.is_dir():
                        return True
        return False

    def _append_index_entry(self, msg: Message, event_file: Path) -> None:
        entry = {
            "msg_id": msg.msg_id,
            "from_agent": msg.from_agent,
            "to_agent": msg.to_agent,
            "timestamp": msg.timestamp,
            "path": event_file.name,
        }
        with self.index_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _read_index_entries(self) -> list[dict]:
        if not self.index_path.exists():
            return []
        entries: list[dict] = []
        for line in self.index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def _load_message_file(self, path: Path) -> Message | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Message(**data)
        except (json.JSONDecodeError, TypeError, KeyError, OSError):
            return None

    def _messages_from_glob_inbox(self, agent_id: str) -> list[Message]:
        messages: list[Message] = []
        for path in self.events_dir.glob("*.json"):
            msg = self._load_message_file(path)
            if msg is not None and msg.to_agent == agent_id:
                messages.append(msg)
        messages.sort(key=lambda m: m.timestamp, reverse=True)
        return messages

    def _messages_from_glob_thread(
        self, from_agent: str, to_agent: str
    ) -> list[Message]:
        messages: list[Message] = []
        for path in self.events_dir.glob("*.json"):
            msg = self._load_message_file(path)
            if msg is None:
                continue
            if (msg.from_agent == from_agent and msg.to_agent == to_agent) or (
                msg.from_agent == to_agent and msg.to_agent == from_agent
            ):
                messages.append(msg)
        messages.sort(key=lambda m: m.timestamp)
        return messages


    def send(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        emotional_tone: str = "neutral",
        canon_refs: list[str] | None = None,
        veil_state: str = "calm",
    ) -> Message:
        if not self._agent_exists(from_agent):
            raise ValueError(
                f"Agent '{from_agent}' does not exist. "
                f"Check 02_agents/ or 13_agents/ directories."
            )
        if not self._agent_exists(to_agent):
            raise ValueError(
                f"Agent '{to_agent}' does not exist. "
                f"Check 02_agents/ or 13_agents/ directories."
            )

        # P2.7: apply Veil-state distortion before persisting
        trust = self._lookup_trust(from_agent, to_agent)
        distorted_content, distortion_label = _apply_distortion(content, veil_state, trust)
        original = content if distortion_label is not None else None

        # Append a monotonic sequence suffix to the ISO timestamp so back-to-back
        # sends within the same microsecond still sort chronologically.
        ts = datetime.now(UTC).isoformat() + f"-{_next_seq():010d}"
        msg = Message(
            msg_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            content=distorted_content,
            emotional_tone=emotional_tone,
            canon_refs=canon_refs or [],
            timestamp=ts,
            original_content=original,
            distortion_applied=distortion_label,
        )

        # Write full message to events dir
        self.events_dir.mkdir(parents=True, exist_ok=True)
        event_file = self.events_dir / f"{msg.msg_id}.json"
        event_file.write_text(
            json.dumps(asdict(msg), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._append_index_entry(msg, event_file)

        # Append summary line to replay.jsonl
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "type": "agent_message",
            "msg_id": msg.msg_id,
            "from": msg.from_agent,
            "to": msg.to_agent,
            "emotional_tone": msg.emotional_tone,
            "distortion": distortion_label,
            "timestamp": msg.timestamp,
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        return msg

    def read_inbox(self, agent_id: str, limit: int = 10) -> list[Message]:
        if not self.events_dir.exists():
            return []
        entries = self._read_index_entries()
        if entries:
            matched = [e for e in entries if e.get("to_agent") == agent_id]
            matched.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
            messages: list[Message] = []
            for entry in matched[:limit]:
                rel = entry.get("path") or f"{entry.get('msg_id')}.json"
                msg = self._load_message_file(self.events_dir / rel)
                if msg is not None:
                    messages.append(msg)
            return messages
        return self._messages_from_glob_inbox(agent_id)[:limit]

    def read_thread(self, from_agent: str, to_agent: str) -> list[Message]:
        if not self.events_dir.exists():
            return []
        entries = self._read_index_entries()
        if entries:
            matched = [
                e
                for e in entries
                if (
                    e.get("from_agent") == from_agent
                    and e.get("to_agent") == to_agent
                )
                or (
                    e.get("from_agent") == to_agent
                    and e.get("to_agent") == from_agent
                )
            ]
            matched.sort(key=lambda e: e.get("timestamp", ""))
            messages: list[Message] = []
            for entry in matched:
                rel = entry.get("path") or f"{entry.get('msg_id')}.json"
                msg = self._load_message_file(self.events_dir / rel)
                if msg is not None:
                    messages.append(msg)
            return messages
        return self._messages_from_glob_thread(from_agent, to_agent)
