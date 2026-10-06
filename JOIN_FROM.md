# Join-from map — what we can take

Sources are operator-local references. Copy into `90_intake/<bucket>/`, then promote. Do not commit bulk intake dumps to the public repo.

Configure local paths via `90_intake/sources.json` (gitignored). Start from [`90_intake/sources.example.json`](90_intake/sources.example.json).

## Source buckets

| Bucket | Typical origin | Best candidates |
|--------|----------------|-----------------|
| `from_the_veil` | clone of `kas1987/The-Veil` | `design/` motif docs, selected persona packages, postgres schema ideas |
| `from_viel_small_town` | clone of `kas1987/Viel-Small-Town` | `00_charter`, `10_canon`, `12_metaphysics`, `01_districts`, `13_agents`, runtime/memory/UI when ready |
| `from_veil_core` | local `veil_core` package | `prism.py`, `revelation.py`, `voice.py`, `db.py` |
| `from_center_mass` | local docs / thin game tree | sister duality scripts; historical sprint docs → `docs/` or `99_archive` |
| `from_zelex_pack` | local sigil pack | SVG / voice assets after review |

## Suggested pull order

1. Canon + metaphysics
2. Charter / gates
3. Motif design
4. Agents + districts
5. Runtime / memory / alignment
6. UI tokens
7. Optional packs / historical docs

## Do not bulk-copy into git

- Entire legacy `agent_*` swarms without picking keepers
- `vendor/`, `.venv`, SQLite DBs, replay junk
- NSFW packs until charter says they belong
- Model weights or private pipeline databases

## Intake command pattern

```powershell
# After copying sources.example.json -> sources.json and filling paths:
.\scripts\intake_copy.ps1 -Source viel_small_town -RelPath 12_metaphysics
# Review under 90_intake/, then promote keepers into the matching numbered plane.
```
