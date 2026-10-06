# Security Policy

## Supported versions

This repository is an active creative scaffold. Security fixes land on `main`.

## Reporting a vulnerability

Please **do not** open a public issue for security reports.

- Prefer [GitHub Security Advisories](https://github.com/kas1987/New_Veil/security/advisories/new) for this repo.
- Or email the account owner via GitHub profile contact options for `kas1987`.

Include:
- description of the issue
- steps to reproduce
- impact assessment
- whether a fix is already known

## Public repo hygiene

- Never commit API keys, tokens, `.env` files, or private model weights.
- Machine-local paths belong in gitignored local overrides (`90_intake/sources.json`), not in tracked docs.
- Intake copies under `90_intake/from_*/` are local staging and are not tracked.
