# Contributing to New_Veil

Thanks for helping build The Veil. This repo is public for review and CI; creative IP still follows canon gates.

## Before you start

1. Read [`AGENTS.md`](AGENTS.md), [`REPO_STATUS.md`](REPO_STATUS.md), and [`CHROMATIC_TREES.md`](CHROMATIC_TREES.md).
2. Canon in `10_canon/` is immutable at runtime. Changes require the review gates in `00_charter/REVIEW_GATES.md`.
3. Prefer small PRs: one district, one agent, one metaphysics doc, or one tooling concern.

## Workflow

```text
fork or branch → change → tests/CI green → pull request → review → squash merge
```

1. Branch from `main`: `feature/<short-name>` or `fix/<short-name>`.
2. Run local checks:

   ```bash
   python scripts/check_scaffold.py
   pre-commit run --all-files   # if installed
   ```

3. Open a PR using the template. Link related issues.
4. Wait for the **CI** workflow. Address review comments.

## Intake from legacy trees

Legacy GitHub clones and disk cousins are **operator-local**. Copy candidates into `90_intake/` on your machine, then promote into numbered planes in the PR. Do not commit bulk intake dumps.

Copy [`90_intake/sources.example.json`](90_intake/sources.example.json) to `90_intake/sources.json` (gitignored) for local paths.

## Code review expectations

- CI must pass.
- No secrets or large binaries.
- CFS plane numbers respected; update the worktree map when structure changes.
- Public docs stay free of private machine paths.

## License

By contributing, you agree your contributions are licensed under the MIT License in [`LICENSE`](LICENSE).
