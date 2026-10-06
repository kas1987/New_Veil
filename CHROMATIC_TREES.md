# ChromaticTrees — `D:\.30_Veil` (scaffold)

Fresh Veil home. Numbered planes only; no Small-Town waivers carried forward.

## Root plane index

| NN | Plane | Folder(s) | Contents |
|----|-------|-----------|----------|
| 00 | Governance | `00_harness/`, `00_charter/` | Harness, charter, review gates |
| 01 | Districts | `01_districts/` | Locations + unlock configs |
| 03 | Memory | `03_memory/` | Schema, router, SQLite |
| 04 | Runtime | `04_runtime/` | Orchestrator, DSSM, veil engine |
| 05 | Alignment | `05_alignment/` | Scorer, quarantine |
| 06 | Logs | `06_logs/` | Replay / validation outputs |
| 07 | UI | `07_ui/` | Observatory + narrative tokens |
| 09 | Registry | `09_registry/` | Worktree maps, SSoT |
| 10 | Canon | `10_canon/` | Immutable canon, lore bible |
| 11 | World | `11_world/` | Cities, factions, followers |
| 12 | Metaphysics | `12_metaphysics/` | Veil, dreams, echoes, states |
| 13 | Agents | `13_agents/` | All agent profiles (no legacy `02_`) |
| 14 | Psychometrics | `14_psychometrics/` | Instruments |
| 15 | Voice | `15_voice/` | Voice / TTS |
| 90 | Intake | `90_intake/` | Staging from legacy sources |
| 99 | Archive | `99_archive/` | Rejected / frozen pulls |

## Allowed root exceptions

| Directory | Purpose |
|-----------|---------|
| `.agents/` | Agent skill pack |
| `docs/` | Published docs |
| `scripts/` | Automation |
| `tests/` | Test suite |
| `design/` | Motif / visual system (pre-UI) |

## Law

One slot, one meaning, one folder. Update `09_registry/09.03_WORKTREE_MAPS/09.03.01_WORKTREE_MAP.json` when planes change.
