"""DSSM L4 — Network Propagation.

Directed weighted graph of agents. After L0 updates a focal agent for the
session, this layer leaks a fraction of the focal agent's stock DELTA
(post - pre) to its neighbors.

Source: Path A canonical L4.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from .models import CoreState, clamp


@dataclass
class Edge:
    src: str
    dst: str
    influence: float = 0.15
    polarity: int = 1  # +1 ally, -1 rival


@dataclass
class Network:
    agents: Dict[str, CoreState] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)

    def add_agent(self, name: str, state: CoreState) -> None:
        self.agents[name] = state

    def add_edge(
        self,
        src: str,
        dst: str,
        influence: float = 0.15,
        polarity: int = 1,
    ) -> None:
        self.edges.append(
            Edge(src=src, dst=dst, influence=influence, polarity=polarity),
        )

    def neighbors_of(self, src: str) -> List[Edge]:
        return [e for e in self.edges if e.src == src]

    def avg_trust(self) -> float:
        return (
            (sum(a.trust for a in self.agents.values()) / len(self.agents))
            if self.agents
            else 0.0
        )

    def avg_affection(self) -> float:
        return (
            (sum(a.affection for a in self.agents.values()) / len(self.agents))
            if self.agents
            else 0.0
        )

    @classmethod
    def from_config(cls, path: str | Path) -> Network:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        net = cls()
        for name, st in data.get("agents", {}).items():
            net.add_agent(name, CoreState(**st))
        for e in data.get("edges", []):
            net.add_edge(
                e["src"],
                e["dst"],
                float(e.get("influence", 0.15)),
                int(e.get("polarity", 1)),
            )
        return net


def propagate(
    network: Network,
    focal: str,
    pre: CoreState,
    post: CoreState,
) -> None:
    """Spill a fraction of the focal agent's per-session delta to neighbors."""
    d_trust = post.trust - pre.trust
    d_affection = post.affection - pre.affection
    d_suspicion = post.suspicion - pre.suspicion

    for edge in network.neighbors_of(focal):
        nb = network.agents.get(edge.dst)
        if nb is None:
            continue
        w = edge.influence
        if edge.polarity > 0:
            nb.trust = clamp(nb.trust + w * 0.6 * d_trust)
            nb.affection = clamp(nb.affection + w * 0.4 * d_affection)
            nb.suspicion = clamp(nb.suspicion + w * 0.3 * d_suspicion)
        else:
            nb.suspicion = clamp(nb.suspicion + w * 0.5 * max(0.0, d_trust))
            nb.resistance = clamp(nb.resistance + w * 0.4 * max(0.0, d_trust))
            if d_trust < 0:
                nb.trust = clamp(nb.trust + w * 0.2 * (-d_trust))
