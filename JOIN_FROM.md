# Join-from map — what we can take

Sources are read-only references. Copy into `90_intake/<bucket>/`, then promote.

## Source buckets

| Bucket | Path | Best candidates |
|--------|------|-----------------|
| `from_the_veil` | `D:\.20_Center_Mass\projects\games\_veil_github_staging\The-Veil` | `design/` motif docs, `agent_lore` / persona packages worth keeping, postgres schema ideas (`veil_init.sql`) — not the flat agent swarm as-is |
| `from_viel_small_town` | `...\Viel-Small-Town` | `00_charter`, `10_canon`, `12_metaphysics`, `01_districts`, `13_agents`, `04_runtime` (DSSM/orchestrator), `07_ui` design tokens, `03_memory` schema — **primary harvest** |
| `from_veil_core` | `D:\.20_Center_Mass\projects\core\production_platform\veil_core` | `prism.py`, `revelation.py`, `voice.py`, `db.py` — small production package |
| `from_center_mass` | `D:\.20_Center_Mass\projects\games\veil` + docs | Sister duality AI scripts under `ai/`; `docs/projects/VEIL_CONTENT_AI_INTEGRATION.md`, `SPRINT_VEIL_AI_OPTIMIZATION.md` → `docs/` or `99_archive` |
| `from_zelex_pack` | `D:\Zelex\Packs\Veil_Sigil_System_MasterPack` | Sigil SVG / voice pack assets after review |
| design skill (optional) | `E:\Claude_Master\skills\veil-design-system` | Cross-check vs Small-Town `07_ui/veil_design_system` |

Machine-readable pointers: [`90_intake/sources.json`](90_intake/sources.json).

## Suggested first pull order

1. **Canon + metaphysics** — Small-Town `10_canon`, `12_metaphysics`  
2. **Charter / gates** — Small-Town `00_charter`  
3. **Motif design** — The-Veil `design/veil_motif_design_doc.md`  
4. **Agents** — Small-Town `13_agents` (+ Mira from `02_agents` if still needed)  
5. **Runtime** — Small-Town `04_runtime` + optionally merge ideas from `veil_core`  
6. **UI tokens** — Small-Town `07_ui/veil_design_system`  
7. **Memory schema** — Small-Town `03_memory`  
8. **Zelex / sister duality / sprint docs** — only if still wanted

## Do not bulk-copy

- Entire `agent_*` swarm from The-Veil without picking keepers  
- `vendor/`, `.venv`, SQLite DBs, `06_logs` replay junk  
- NSFW agent packs until charter says they belong  
- Comfy weights or `.000_AI` pipeline DBs  

## Intake command pattern

```powershell
$src  = 'D:\.20_Center_Mass\projects\games\_veil_github_staging\Viel-Small-Town\12_metaphysics'
$dest = 'D:\.30_Veil\90_intake\from_viel_small_town\12_metaphysics'
Copy-Item -Recurse -Force $src $dest
# review, then move keepers into D:\.30_Veil\12_metaphysics\
```
