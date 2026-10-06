"""Relationship graph for Veil Town — SQLite-backed, physics via vendored DSSM.

Architecture: in-memory state is the full 4-stock prism_dssm.CoreState
(trust, affection, suspicion, resistance) so apply_deltas + DarkQuasar work.
On-disk schema persists only the 3 player-facing stocks. Resistance is
reconstituted at a sane default on read.

Schema (03_memory/schema.sql relationships table):
agent_a, agent_b (UNIQUE pair), trust, affection, suspicion,
interactions, last_interaction.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Vendored DSSM engine — repo-relative path
_HERE = Path(__file__).resolve().parent
_DSSM_SRC = _HERE / "dssm_engine" / "src"
if _DSSM_SRC.exists() and str(_DSSM_SRC) not in sys.path:
    sys.path.insert(0, str(_DSSM_SRC))

from prism_dssm.dssm_core import apply_deltas, decay_step  # noqa: E402
from prism_dssm.models import CoreParams, CoreState, Signal, VeilState  # noqa: E402
from prism_dssm.veil_effects import DarkQuasar, EntropyEngine  # noqa: E402

_DEFAULT_DB = _HERE.parent / "03_memory" / "veil_town.sqlite"
_DEFAULT_RESISTANCE = 50.0


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class RelationshipEdge:
    agent_a: str
    agent_b: str
    state: CoreState = field(default_factory=CoreState)
    interactions: int = 0
    last_interaction: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "state": self.state.as_dict(),
            "interactions": self.interactions,
            "last_interaction": self.last_interaction,
        }


def _row_to_edge(row: sqlite3.Row) -> RelationshipEdge:
    state = CoreState(
        trust=row["trust"],
        affection=row["affection"],
        suspicion=row["suspicion"],
        resistance=_DEFAULT_RESISTANCE,
    )
    return RelationshipEdge(
        agent_a=row["agent_a"],
        agent_b=row["agent_b"],
        state=state,
        interactions=row["interactions"] if row["interactions"] is not None else 0,
        last_interaction=row["last_interaction"] or "",
    )


class VeilTownGraph:
    """SQLite-backed relationship graph using vendored DSSM physics."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._quasar = DarkQuasar()
        self._entropy = EntropyEngine()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def set(
        self,
        agent_a: str,
        agent_b: str,
        state: CoreState,
        interactions: int | None = None,
    ) -> None:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT interactions FROM relationships WHERE agent_a=? AND agent_b=?",
                (agent_a, agent_b),
            ).fetchone()
            final_interactions = (
                interactions
                if interactions is not None
                else (existing["interactions"] if existing else 0)
            )
            conn.execute(
                """
                INSERT INTO relationships
                    (agent_a, agent_b, trust, affection, suspicion,
                     interactions, last_interaction, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_a, agent_b) DO UPDATE SET
                    trust=excluded.trust,
                    affection=excluded.affection,
                    suspicion=excluded.suspicion,
                    interactions=excluded.interactions,
                    last_interaction=excluded.last_interaction,
                    updated_at=excluded.updated_at
                """,
                (
                    agent_a,
                    agent_b,
                    state.trust,
                    state.affection,
                    state.suspicion,
                    final_interactions,
                    _now_iso(),
                    _now_iso(),
                ),
            )

    def get(self, agent_a: str, agent_b: str) -> RelationshipEdge | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM relationships WHERE agent_a=? AND agent_b=?",
                (agent_a, agent_b),
            ).fetchone()
        return _row_to_edge(row) if row else None

    def apply_signal(
        self, agent_a: str, agent_b: str, signal: Signal
    ) -> RelationshipEdge:
        """Apply DSSM Signal: L0 deltas (Resistance-gated) + L3c DarkQuasar gravity."""
        edge = self.get(agent_a, agent_b)
        if edge is None:
            edge = RelationshipEdge(agent_a=agent_a, agent_b=agent_b, state=CoreState())

        state = edge.state
        params = CoreParams()
        apply_deltas(state, signal.to_dict(), params)

        excess = self._quasar.assess(state)
        if excess > 0.0:
            self._quasar.apply_gravity(state, excess)

        edge.interactions += 1
        edge.last_interaction = _now_iso()
        edge.state = state
        self.set(agent_a, agent_b, state, interactions=edge.interactions)
        return edge

    def decay_all(self, veil_state: VeilState | None = None) -> None:
        multiplier = self._entropy.decay_multiplier()
        if veil_state is not None:
            multiplier *= veil_state.entropy_multiplier

        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM relationships").fetchall()

        params = CoreParams()
        for row in rows:
            edge = _row_to_edge(row)
            state = edge.state
            decay_step(state, params, multiplier)
            self.set(edge.agent_a, edge.agent_b, state, interactions=edge.interactions)

    def neighbors(self, agent_id: str) -> list[RelationshipEdge]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM relationships WHERE agent_a=? OR agent_b=?",
                (agent_id, agent_id),
            ).fetchall()
        return [_row_to_edge(r) for r in rows]

    def to_dict(self) -> dict:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM relationships").fetchall()
        agents: dict[str, dict] = {}
        edges: list[dict] = []
        for row in rows:
            edge = _row_to_edge(row)
            for name in (edge.agent_a, edge.agent_b):
                if name not in agents:
                    agents[name] = edge.state.as_dict()
            edges.append(
                {
                    "src": edge.agent_a,
                    "dst": edge.agent_b,
                    "trust": edge.state.trust,
                    "affection": edge.state.affection,
                    "suspicion": edge.state.suspicion,
                    "interactions": edge.interactions,
                }
            )
        return {"agents": agents, "edges": edges}

    @classmethod
    def from_follower_graph(
        cls, path: Path, db_path: Path | None = None
    ) -> VeilTownGraph:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        graph = cls(db_path=db_path)
        agent_states: dict[str, CoreState] = {}
        for name, vals in data.get("agents", {}).items():
            agent_states[name] = CoreState(
                trust=float(vals.get("trust", 30.0)),
                affection=float(vals.get("affection", 25.0)),
                suspicion=float(vals.get("suspicion", 50.0)),
                resistance=float(vals.get("resistance", _DEFAULT_RESISTANCE)),
            )
        for edge_def in data.get("edges", []):
            src = edge_def["src"]
            dst = edge_def["dst"]
            state = agent_states.get(src, CoreState())
            graph.set(agent_a=src, agent_b=dst, state=state)
        return graph
