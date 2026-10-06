# Agent Rules — New_Veil (`kas1987/New_Veil`)

1. This repository is a **new public scaffold**. Do not treat `kas1987/The-Veil` or `kas1987/Viel-Small-Town` as live code parents.
2. **Intake first.** Anything brought from legacy lands in local `90_intake/` before it may enter a numbered plane. Do not commit bulk intake dumps.
3. **Canon is sacred once promoted.** After material is in `10_canon/`, changes need an explicit review gate (see `00_charter/`).
4. **One concern per change** — one district, one agent, one metaphysics doc, or one runtime module.
5. **Do not commit secrets.** No API keys, Discord tokens, or `.env` with credentials.
6. **Prefer promote over merge.** Legacy repos stay frozen references configured in local `90_intake/sources.json`.
7. **CFS numbering.** New project-owned folders use the plane table in `CHROMATIC_TREES.md`. Update `09_registry/09.03_WORKTREE_MAPS/09.03.01_WORKTREE_MAP.json` when adding planes.
8. **Outputs** go under `06_logs/` or transient runtime state — keep root and canon clean.
9. **Comfy / Art image work** stays coordinated with an operator-local Comfy hub (`VEIL_COMFY_HUB` if set). Do not copy pipeline weights into this tree.
10. Prefer PRs into `main` so Actions and review run. Commit/push only when the user asks, unless they said GO on a scoped task.

## Default loop

```text
JOIN_FROM → 90_intake (local) → review → numbered plane → PR → CI → merge
```
