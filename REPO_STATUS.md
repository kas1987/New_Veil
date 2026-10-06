# Repo Status — New_Veil

| Field | Value |
|-------|-------|
| **Status** | `ACTIVE_SCAFFOLD` |
| **Registry ID** | `REPO-VEIL-30` |
| **GitHub** | [kas1987/New_Veil](https://github.com/kas1987/New_Veil) |
| **Visibility** | public |
| **Role** | Fresh product home for The Veil — selective reuse of legacy material |
| **Legacy remotes** | `kas1987/The-Veil` (old flagship), `kas1987/Viel-Small-Town` (old playground) |

## Policy vs old repos

| Old claim | New stance |
|-----------|------------|
| The-Veil = canonical flagship | Historical only until content is promoted here |
| Viel-Small-Town = do-not-merge playground | Still true for *that* repo; this root is the new join target |
| Promote subsystems selectively | **Yes** — via local `90_intake/` into this tree |

## Promoted (2026-10-05)

- `design/` ← The-Veil motif design
- `12_metaphysics/` ← Viel-Small-Town
- `00_charter/` ← Viel-Small-Town
- `10_canon/` ← Viel-Small-Town
- `13_agents/` ← sisters / supporting / whispertech + Mira (from legacy `02_agents`)
- `01_districts/` ← Caetherra, Ashveil, Ember Vaults, Stillward, The Hollow + unlock engine

## Public engineering

- MIT license
- CI scaffold gate + pre-commit
- CodeQL (Python)
- Dependabot for GitHub Actions
- PR/issue templates, CODEOWNERS, SECURITY.md, CONTRIBUTING.md
- Branch protection ruleset on `main`

## Not yet

- Runnable simulation bootstrap
- Runtime / memory / alignment / UI planes

## Next

1. Intake `04_runtime` + `03_memory` (+ `05_alignment`) when ready to run.
2. Intake `11_world` / `07_ui` as needed.
