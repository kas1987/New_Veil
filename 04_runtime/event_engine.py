"""Veil Town — Dream-State and Symbolic Event Engine.

Generates dream states, fires echoes, schedules symbolic events,
and filters rendered object lists by player depth.

Architectural notes:
- hidden_truth is STORED in DreamState but callers MUST check depth > 0.7
  before exposing to any UI layer (render-time gate, not generation-time).
- echo.distortion_level is DERIVED at query time, never stored.
- void_door is ABSENT from rendered lists when depth < 0.75 (not shown as
  locked — removed entirely).
- convergence dream requires depth_authentic=True behavioral flag.
- corruption_dream sets corruption_flight_lockout_until on session state;
  callers track flight attempts.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from veil_loader import load_module

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class SymbolicEvent:
    event_id: str
    event_type: Literal["dream", "echo", "vision", "convergence"]
    trigger_condition: str
    payload: dict
    revealed_canon_id: str | None = None
    depth_threshold: float = 0.0


@dataclass
class DreamState:
    dream_id: str
    agent_id: str
    dream_type: Literal["memory_echo", "prophecy", "corruption_dream", "convergence"]
    content: str
    depth: float
    # NOTE: callers must check depth > 0.7 before exposing hidden_truth to any UI layer.
    hidden_truth: str | None = None


# ---------------------------------------------------------------------------
# EventEngine
# ---------------------------------------------------------------------------


class EventEngine:
    """Runtime engine for symbolic events, dreams, and echoes."""

    def __init__(self, project_root: Path | None = None) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent

        self._project_root = project_root
        self._log_path = project_root / "06_logs" / "replay.jsonl"
        self._consumed_path = project_root / "06_logs" / "consumed_symbolic_events.json"
        self._registry_path = (
            project_root / "12_metaphysics" / "symbolic_object_registry.json"
        )
        self._consumed_ids = self._load_consumed_ids()

        # Load symbolic object registry (graceful fallback)
        self._registry: dict = {}
        if self._registry_path.exists():
            try:
                raw = json.loads(self._registry_path.read_text(encoding="utf-8"))
                # Index by object id for fast lookup
                self._registry = {obj["id"]: obj for obj in raw.get("objects", [])}
            except (json.JSONDecodeError, KeyError):
                self._registry = {}

        # Event queue: list of (trigger_at_depth, event)
        self._queue: list[tuple[float, SymbolicEvent]] = []

        # Load seeded scheduled events (graceful fallback if file missing)
        seed_path = project_root / "12_metaphysics" / "scheduled_events.json"
        if seed_path.exists():
            try:
                raw = json.loads(seed_path.read_text(encoding="utf-8"))
                for ev in raw.get("events", []):
                    self._queue.append(
                        (
                            float(ev.get("trigger_at_depth", 0.0)),
                            SymbolicEvent(
                                event_id=ev["event_id"],
                                event_type=ev.get("event_type", "vision"),
                                trigger_condition=ev.get("trigger_condition", ""),
                                payload=ev.get("payload", {}),
                                revealed_canon_id=ev.get("revealed_canon_id"),
                                depth_threshold=float(ev.get("trigger_at_depth", 0.0)),
                            ),
                        )
                    )
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # fall through with empty queue

        self._queue = [
            (threshold, event)
            for threshold, event in self._queue
            if event.event_id not in self._consumed_ids
        ]

        # Load memory_router via cache-safe loader
        memory_path = project_root / "03_memory" / "memory_router.py"
        try:
            self._memory = load_module("memory_router", memory_path)
        except Exception:
            self._memory = None

    # ------------------------------------------------------------------
    # Scheduling
    # ------------------------------------------------------------------

    def schedule(self, event: SymbolicEvent, trigger_at_depth: float) -> None:
        """Queue a symbolic event to fire when current_depth >= trigger_at_depth."""
        if event.event_id in self._consumed_ids:
            return
        self._queue.append((trigger_at_depth, event))

    def preview_events(
        self, current_depth: float, limit: int | None = None
    ) -> list[SymbolicEvent]:
        """Return the events that would fire at the given depth without consuming them."""
        events = [event for threshold, event in self._queue if threshold <= current_depth]
        if limit is not None:
            return events[:limit]
        return events

    def tick(self, current_depth: float, agent_id: str) -> list[SymbolicEvent]:
        """Fire all queued events whose threshold has been reached.

        Fired events are removed from the queue and appended to replay.jsonl.
        Returns the list of fired SymbolicEvent objects.
        """
        fired: list[SymbolicEvent] = []
        remaining: list[tuple[float, SymbolicEvent]] = []

        for threshold, event in self._queue:
            if threshold <= current_depth:
                fired.append(event)
                self._log_event(
                    {
                        "type": "symbolic_event",
                        "event_id": event.event_id,
                        "event_type": event.event_type,
                        "agent_id": agent_id,
                        "depth": current_depth,
                    }
                )
            else:
                remaining.append((threshold, event))

        self._queue = remaining
        if fired:
            for event in fired:
                self._consumed_ids.add(event.event_id)
            self._save_consumed_ids()
        return fired

    def _load_consumed_ids(self) -> set[str]:
        if not self._consumed_path.is_file():
            return set()
        try:
            raw = json.loads(self._consumed_path.read_text(encoding="utf-8"))
            return {str(item) for item in raw.get("event_ids", [])}
        except (json.JSONDecodeError, TypeError, OSError):
            return set()

    def _save_consumed_ids(self) -> None:
        self._consumed_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event_ids": sorted(self._consumed_ids),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        tmp_path = self._consumed_path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp_path.replace(self._consumed_path)

    # ------------------------------------------------------------------
    # Dream generation
    # ------------------------------------------------------------------

    def generate_dream(
        self,
        agent_id: str,
        depth: float,
        depth_authentic: bool = False,
        llm_callable=None,
    ) -> DreamState:
        """Generate a DreamState appropriate to the current depth level.

        dream_type selection:
          depth < 0.40                          → memory_echo
          0.40 <= depth < 0.65                  → prophecy
          0.65 <= depth < 0.85                  → corruption_dream (default for this band)
          depth >= 0.85 and depth_authentic=True → convergence
          depth >= 0.85 and depth_authentic=False → prophecy (convergence blocked)
        """
        # Determine dream_type
        if depth < 0.40:
            dream_type: Literal[
                "memory_echo", "prophecy", "corruption_dream", "convergence"
            ] = "memory_echo"
        elif depth < 0.65:
            dream_type = "prophecy"
        elif depth < 0.85:
            dream_type = "corruption_dream"
        else:
            dream_type = "convergence" if depth_authentic else "prophecy"

        # Load recent memories for this agent
        memories: list[dict] = []
        if self._memory is not None:
            try:
                recent = self._memory.read_recent_memories(limit=10)
                memories = [m for m in recent if m.get("agent_id") == agent_id][:3]
            except Exception:
                memories = []

        # Generate content — LLM if available, template otherwise
        content = self._generate_dream_content(
            dream_type, agent_id, depth, memories, llm_callable
        )

        # hidden_truth: only populate when depth > 0.7
        hidden_truth: str | None = None
        if depth > 0.7:
            hidden_truth = "The truth is visible to those who earned it."

        dream = DreamState(
            dream_id=str(uuid.uuid4()),
            agent_id=agent_id,
            dream_type=dream_type,
            content=content,
            depth=depth,
            hidden_truth=hidden_truth,
        )

        self._log_event(
            {
                "type": "dream_generated",
                "dream_id": dream.dream_id,
                "agent_id": agent_id,
                "dream_type": dream_type,
                "depth": depth,
            }
        )

        return dream

    def _generate_dream_content(
        self,
        dream_type: str,
        agent_id: str,
        depth: float,
        memories: list[dict],
        llm_callable=None,
    ) -> str:
        """Generate dream content. If llm_callable is provided, use it for
        atmospheric narrative; otherwise fall back to templates.

        llm_callable signature: (agent_id, user_prompt) -> {"output": str, ...}
        """
        if llm_callable is not None:
            try:
                memory_summary = (
                    " | ".join(str(m.get("content", ""))[:80] for m in memories[:3])
                    or "(no prior memories surfaced yet)"
                )
                prompt = (
                    f"You are dreaming as {agent_id}. Dream-type is '{dream_type}'. "
                    f"Current emotional depth: {depth:.2f}. "
                    f"Recent memory fragments: {memory_summary}\n\n"
                    f"Compose a single atmospheric paragraph (2-4 sentences) as the "
                    f"dream's symbolic content. Use imagery appropriate to the type: "
                    f"memory_echo replays a past fragment distorted; prophecy reveals "
                    f"a possible future symbolically; corruption_dream surfaces shadow "
                    f"and fear; convergence brings both Sisters to the threshold."
                )
                result = llm_callable(agent_id, prompt)
                text = (result or {}).get("output", "").strip()
                if text:
                    return text
            except Exception:
                pass  # fall through to template

        # Template fallback
        if dream_type == "memory_echo":
            if memories:
                fragment = str(memories[0].get("content", ""))[:60]
                return f"A fragment surfaces: {fragment}..."
            return "A fragment surfaces: something half-remembered, already fading..."

        if dream_type == "prophecy":
            if depth < 0.5:
                symbol = "a door with no handle"
            elif depth < 0.7:
                symbol = "two lanterns where there should be one"
            else:
                symbol = "the Veil itself, folded like cloth"
            return (
                f"The Veil shows something that has not yet happened. "
                f"[Symbolic placeholder based on depth level]: {symbol}."
            )

        if dream_type == "corruption_dream":
            turning_point = "the light inverts"
            return (
                f"The darkness has weight. {agent_id} sees {turning_point}. "
                f"Something that should be familiar turns wrong."
            )

        # convergence
        return "Both sisters stand at the threshold. The Veil thins to nothing."

    # ------------------------------------------------------------------
    # Echo generation
    # ------------------------------------------------------------------

    def fire_echo(self, agent_id: str, memory_id: int) -> str:
        """Fire an echo based on a specific memory record.

        Distortion formula (derived at query time, never stored):
          distortion = min(1.0,
              memory.emotional_weight * 0.3 + corruption_level * 0.7)
          Falls back to 0.2 if those fields are absent.
        """
        memory_record: dict = {}
        if self._memory is not None:
            try:
                recent = self._memory.read_recent_memories(limit=50)
                # Try to find by id; fall back to most recent
                matched = [m for m in recent if m.get("id") == memory_id]
                if matched:
                    memory_record = matched[0]
                elif recent:
                    memory_record = recent[0]
            except Exception:
                memory_record = {}

        # Compute distortion_level (derived, never stored)
        emotional_weight = memory_record.get("emotional_weight")
        corruption_level = memory_record.get("corruption_level")
        if emotional_weight is not None and corruption_level is not None:
            distortion_level = min(1.0, emotional_weight * 0.3 + corruption_level * 0.7)
        else:
            distortion_level = 0.2

        # Generate echo content
        raw_content = memory_record.get("content", "A memory without shape.")
        if distortion_level < 0.3:
            echo_content = f"[Echo — near-accurate replay] {raw_content}"
        else:
            echo_content = (
                f"[Echo — symbolic distortion {distortion_level:.2f}] "
                f"The corridor again. But the corridor is wrong. "
                f"Something from {agent_id}'s past replays with inverted geometry. "
                f"The emotional shape is preserved; the literal facts are unreliable."
            )

        self._log_event(
            {
                "type": "echo_fired",
                "agent_id": agent_id,
                "source_memory_id": memory_id,
                "distortion_level": distortion_level,
                "unreliable": distortion_level > 0.7,
            }
        )

        return echo_content

    # ------------------------------------------------------------------
    # Object rendering
    # ------------------------------------------------------------------

    def filter_objects_for_depth(self, objects: list[str], depth: float) -> list[str]:
        """Return objects visible at the given depth.

        Objects with render_rule="ABSENT_BELOW_THRESHOLD" and
        depth_required > current depth are removed entirely from the list.
        The void_door specifically disappears when depth < 0.75.
        """
        filtered: list[str] = []
        for obj_id in objects:
            obj_def = self._registry.get(obj_id)
            if obj_def is None:
                # Unknown objects pass through unchanged
                filtered.append(obj_id)
                continue
            render_rule = obj_def.get("render_rule", "")
            depth_required = obj_def.get("depth_required", 0.0)
            if render_rule == "ABSENT_BELOW_THRESHOLD" and depth < depth_required:
                # Strip entirely — do not show as locked
                continue
            filtered.append(obj_id)
        return filtered

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_event(self, event: dict) -> None:
        """Append a JSONL line to replay.jsonl with a UTC timestamp."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        event["timestamp"] = datetime.now(UTC).isoformat()
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
