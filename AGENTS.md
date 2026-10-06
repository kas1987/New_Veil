# Agent Rules — The Veil (`D:\.30_Veil`)

1. This root is a **new scaffold**. Do not treat `kas1987/The-Veil`, `kas1987/Viel-Small-Town`, or Center_Mass paths as live code parents.
2. **Intake first.** Anything brought from legacy lands in `90_intake/` before it may enter a numbered plane.
3. **Canon is sacred once promoted.** After material is in `10_canon/`, changes need an explicit review gate (see `00_charter/` when populated).
4. **One concern per change** — one district, one agent, one metaphysics doc, or one runtime module.
5. **Do not commit secrets.** No API keys, Discord tokens, or `.env` with credentials.
6. **Prefer promote over merge.** Old repos stay frozen references under `_veil_github_staging` and disk cousins listed in `JOIN_FROM.md`.
7. **CFS numbering.** New project-owned folders use the plane table in `CHROMATIC_TREES.md`. Update `09_registry/09.03_WORKTREE_MAPS/09.03.01_WORKTREE_MAP.json` when adding planes.
8. **Outputs** go under `06_logs/` or transient runtime state — keep root and canon clean.
9. **Comfy / Art image work** stays coordinated with `D:\.000_AI` (ComfyUI-Art). Do not copy pipeline weights into this tree.
10. Commit only when asked. Push only when asked.

## Default loop

```text
JOIN_FROM → 90_intake → review → numbered plane → registry update → tests/logs
```
