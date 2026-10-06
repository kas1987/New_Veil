# New_Veil

[![CI](https://github.com/kas1987/New_Veil/actions/workflows/ci.yml/badge.svg)](https://github.com/kas1987/New_Veil/actions/workflows/ci.yml)
[![CodeQL](https://github.com/kas1987/New_Veil/actions/workflows/codeql.yml/badge.svg)](https://github.com/kas1987/New_Veil/actions/workflows/codeql.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Fresh public scaffold for **The Veil**. Older GitHub trees are **sources**, not parents. Pull what earns a place; leave the rest.

| | |
|---|---|
| **GitHub** | [kas1987/New_Veil](https://github.com/kas1987/New_Veil) |
| **Status** | `ACTIVE_SCAFFOLD` — charter, canon, agents, districts, runtime, memory, alignment, UI promoted |
| **Intake** | [`90_intake/`](90_intake/) → review → promote into numbered planes |
| **Contribute** | [`CONTRIBUTING.md`](CONTRIBUTING.md) · [`SECURITY.md`](SECURITY.md) |

## Quick map

| Plane | Role |
|---|---|
| `00_charter` / `00_harness` | Constitution, review gates, harness |
| `01_districts` | Places + unlock gates |
| `03_memory` | Memory schema / store |
| `04_runtime` | Orchestrator, DSSM, veil engine |
| `05_alignment` | Scorer / quarantine |
| `06_logs` | Replay + validation outputs |
| `07_ui` | Observatory / narrative UI |
| `09_registry` | Worktree maps, SSoT pointers |
| `10_canon` | Immutable canon + lore bible |
| `11_world` | Cities, factions, followers |
| `12_metaphysics` | Veil states, dreams, echoes |
| `13_agents` | Sister + supporting profiles |
| `14_psychometrics` | Instruments |
| `15_voice` | Voice / TTS surface |
| `90_intake` | Local staging from legacy sources (not tracked) |
| `99_archive` | Rejected or frozen pulls |
| `design` | Motif / visual system |

## Local setup

```bash
git clone https://github.com/kas1987/New_Veil.git
cd New_Veil
python scripts/check_scaffold.py
pip install pre-commit && pre-commit install
```

For selective intake from legacy clones:

```bash
cp 90_intake/sources.example.json 90_intake/sources.json
# edit sources.json with your local paths
```

## Workflow

1. Read [`JOIN_FROM.md`](JOIN_FROM.md) for source inventory.
2. Copy a candidate into local `90_intake/<source>/` (gitignored).
3. Review → promote into the matching numbered plane.
4. Open a PR; CI must pass.

See [`AGENTS.md`](AGENTS.md) and [`REPO_STATUS.md`](REPO_STATUS.md).
