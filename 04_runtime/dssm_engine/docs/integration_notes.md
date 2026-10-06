# Integration Notes

## Convergence Source Map

This tree merges three parallel `/rpi` lifecycles:

| Canonical File                         | Source Path                                  | Notes |
|----------------------------------------|----------------------------------------------|-------|
| `src/prism_dssm/dssm_core.py`          | Path A `path_a_system_first/dssm_core.py`    | L0 chosen for empirically verified R-dissolves-T closure (T=28→99, R=72→0). |
| `src/prism_dssm/persona_filters.py`    | Path B `persona_filter.py` + `attachment_modifier.py` | Merged L1 + L2 (both small, share `PersonaConfig`). |
| `src/prism_dssm/narrative_overrides.py`| Path B `narrative_overrides.py`              | L5 — supports 5 effect kinds. |
| `src/prism_dssm/veil_effects.py`       | Path C `entropy_engine.py` + `signal_corruption.py` + `dark_quasar.py` + `veil_state_machine.py` | Collapsed into one L3 module with sub-headers L3a/L3b/L3c. |
| `src/prism_dssm/network.py`            | Path A `network_graph.py`                    | L4 — directed weighted graph with ally/rival polarity. |
| `configs/personas.json`                | Path B per-persona JSONs                     | Consolidated 4 personas under one `personas` array. |
| `configs/veil_states.json`             | Path C `veil_states.json` + Path A schema    | Path C schedule kept; Path A's quasar fields merged in. |
| `configs/follower_graph.json`          | Path A `network_topology.json`               | Player-centric ally/rival lattice. |

## API Boundaries

- **L0 entry points:** `apply_signal(state, signal: float, params)` (scalar pipeline) **and** `apply_deltas(state, deltas: Dict[str,float], params)` (vector pipeline). The runner uses the dict path; the scalar path is kept for unit-testing the closure.
- **`Signal` dataclass** (`models.py`) is the bridge: dict layers can call `Signal.from_dict(...).to_dict()` if they need the typed form.
- **`VeilState`** is defined once in `models.py`; `_veil_from_dict()` parses both Path-C-style (`veil_state` key) and Path-A-style (`name` key) JSON shapes.

## Pipeline Order

```
L1 filter_signal
  → L2 apply_attachment
  → L3a corrupt_deltas
  → L5 pre_apply
  → L0 apply_deltas              # only L0 mutates the focal CoreState here
  → L3b decay_step(decay_multiplier=entropy.decay_multiplier())
  → L3c quasar.apply_gravity     # in-place drag at high Trust
  → L5 post_apply + tick_pending # delayed effects fire
  → (optional) L4 propagate
```

## Stress Test Sweep

`stress_test_runner.sweep()` walks every persona × ratio × seed cell and emits a win-rate table to `results/sweep_summary.json`. Default cell volume: 4 personas × 6 ratios × 5 seeds = 120 trials × 50 sessions = 6,000 stepped sessions.
