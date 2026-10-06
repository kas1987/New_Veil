# Agent Layer Ownership

| Layer | Module                                | Owner Concern                              | Mutates State? |
|------:|---------------------------------------|--------------------------------------------|----------------|
| L0    | `dssm_core.py`                        | Pure stocks/flows physics                  | Yes (in-place) |
| L1    | `persona_filters.filter_signal`       | Raw signal → per-stock delta dict          | No (returns)   |
| L2    | `persona_filters.apply_attachment`    | Anxious/avoidant/secure multipliers        | No (returns)   |
| L3a   | `veil_effects.corrupt_deltas`         | Per-tick noise on incoming deltas          | No (returns)   |
| L3b   | `veil_effects.EntropyEngine`          | Per-tick decay multiplier                  | No (returns)   |
| L3c   | `veil_effects.DarkQuasar`             | Emotional gravity drag at high Trust       | Yes (in-place) |
| L4    | `network.propagate`                   | Spill focal delta to neighbors (wired in `stress_test_runner.run_trial` when `network` kwarg supplied; sweep auto-loads from `follower_graph.json`) | Yes (in-place) |
| L5    | `narrative_overrides.{pre,post,tick}` | Archetype rule overrides + delayed effects | No (returns)   |

## Rules

- **L0 stays clean.** No persona names, no archetype logic, no narrative branching ever lands in `dssm_core.py`. Layer above to change behavior.
- **JSON > code.** Adding a new Sister is a single `personas.json` entry — no module change.
- **Pipeline order** (per session, per focal): L1 → L2 → L3a → L5 pre → L0 → L3b → L3c → L5 post → L5 tick → (optional L4 propagate).
- **Determinism.** Each effect engine takes its own `random.Random` so seeds are reproducible per run.
- **Win condition** (`models.CoreState.win_condition`): `T > 60 ∧ S < 40 ∧ R < 35`. Do not relax without an entry in `docs/repair_notes.md`.
