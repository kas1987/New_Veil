"""Convenience JSON loaders. Keeps file IO out of math modules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .models import VeilState
from .network import Network
from .persona_filters import PersonaConfig
from .veil_effects import _veil_from_dict


@dataclass
class LoadedConfig:
    personas: Dict[str, PersonaConfig]
    veil_states: List[VeilState]
    veil_schedule: List[str]
    network: Network | None
    stress_test: Dict[str, Any]


def load_config_dir(config_dir: str | Path) -> LoadedConfig:
    """Load every JSON in the canonical configs/ tree."""
    d = Path(config_dir)

    personas_raw = json.loads((d / "personas.json").read_text(encoding="utf-8"))
    personas = {
        p["persona"]: PersonaConfig(persona=p["persona"], raw=p)
        for p in personas_raw["personas"]
    }

    veil_raw = json.loads((d / "veil_states.json").read_text(encoding="utf-8"))
    veil_states = [_veil_from_dict(s) for s in veil_raw["states"]]
    veil_schedule = veil_raw.get("schedule", [s.name for s in veil_states])

    graph_path = d / "follower_graph.json"
    network = Network.from_config(graph_path) if graph_path.exists() else None

    st_path = d / "stress_test_default.json"
    stress = json.loads(st_path.read_text(encoding="utf-8")) if st_path.exists() else {}

    return LoadedConfig(
        personas=personas,
        veil_states=veil_states,
        veil_schedule=veil_schedule,
        network=network,
        stress_test=stress,
    )
