# Repo Status - New_Veil

| Field | Value |
|-------|-------|
| **Status** | `ACTIVE_SCAFFOLD` |
| **Registry ID** | `REPO-VEIL-30` |
| **GitHub** | [kas1987/New_Veil](https://github.com/kas1987/New_Veil) |
| **Visibility** | public |
| **Role** | Fresh product home for The Veil - selective reuse of legacy material |
| **Legacy remotes** | `kas1987/The-Veil` (old flagship), `kas1987/Viel-Small-Town` (old playground) |

## Policy vs old repos

| Old claim | New stance |
|-----------|------------|
| The-Veil = canonical flagship | Historical only until content is promoted here |
| Viel-Small-Town = do-not-merge playground | Still true for *that* repo; this root is the new join target |
| Promote subsystems selectively | **Yes** - via local `90_intake/` into this tree |

## Promoted & Consolidated (2026-11-23 — RPG Vertical Slice)

- `02_systems/` — RPG quests, items/symbolic objects, Resonance Trials, Echo economy
- `11_world/` — World hierarchy (regions, cities, towns, districts, POIs, travel graph, factions)
- `13_agents/` — Unified 15-character roster (`roster_index.json`), completed Nine Sisters (`ashara`, `nyth`, `thessa`) + Solstice Crossing merchant
- `14_psychometrics/` — RPG attributes (`Clarity`, `Empathy`, `Resolve`, `Perception`, `Veil Attunement`) & Resonance tiers
- `15_voice/` — Character voice & mood cue registry
- `03_memory/schema.sql` — Extended with RPG world, stats, inventory, quests, factions, and save slots
- `04_runtime/game_api/` — Unified FastAPI RPG engine + optional local media/portrait adapter
- `07_ui/game_client/` — Interactive Vite + React + TypeScript RPG client built on VEIL Design System
- `pyproject.toml` & `tests/` — Unified Python packaging and end-to-end RPG vertical slice tests

## Promoted (2026-10-05)

- `design/` ← The-Veil motif design
- `12_metaphysics/` ← Viel-Small-Town
- `00_charter/` ← Viel-Small-Town
- `10_canon/` ← Viel-Small-Town
- `13_agents/` ← sisters / supporting / whispertech + Mira (from legacy `02_agents`)
- `01_districts/` ← Caetherra, Ashveil, Ember Vaults, Stillward, The Hollow + unlock engine
- `03_memory/` ← schema + router (event dumps excluded)
- `04_runtime/` ← orchestrator, DSSM, narrative/veil engines + `veil_core`
- `05_alignment/` ← scorer, quarantine, rules
- `07_ui/` ← Gradio observatory, hero, MetaChromatic / Veil design systems

## Public engineering

- MIT license
- CI scaffold gate + pre-commit + Ruff lint
- Python `pytest` + coverage gate (including RPG vertical slice, psychometrics calibration evals, and observatory data layer)
- Frontend `tsc` + Vitest coverage + Vite build + Playwright full-stack E2E browser smoke test
- CodeQL (`python` and `javascript-typescript`)
- Dependabot for GitHub Actions, Python (`pip`), and Frontend (`npm` with grouped Vite/Vitest stack)
- PR/issue templates, CODEOWNERS, SECURITY.md, CONTRIBUTING.md
- Branch protection ruleset on `main` (requiring scaffold, pre-commit, unit tests, frontend UI, Playwright E2E, Review Loopback Gate, and CodeQL)

## Not yet

- Hosted TTS audio generation in `15_voice/` (voice registry & mood cues are promoted; local TTS engine wiring pending)
- Public deployment / auth beyond local single-player SQLite state

## Next

1. Complete `relationships.json` and `system_prompt.md` parity across all `13_agents/` entries.
2. Wire optional TTS synthesis adapter under `15_voice/` (keep machine-local forwarders out of repo).
