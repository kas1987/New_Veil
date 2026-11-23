---
status: accepted
---

# Single-File SQLite Persistence With Forward Schema Migrations

Game state, DSSM relationships, save slots, and encounter arcs persist in a single SQLite file via explicit parameterized SQL (`03_memory/schema.sql`) and inline `_init_db()` / `_load_game()` forward migrations rather than an external database or ORM. Test suites and psychometric evals reuse the exact same schema and migration code over `:memory:` connections.

## Considered Options

- **ORM + Alembic/PostgreSQL:** Adds heavy local setup and migration boilerplate for a single-player local-first desktop vertical slice.
- **JSON save files only:** Loses atomic relational integrity across shared memories, quarantine logs, and relationship matrices.

## Consequences

- New `player_stats` columns and scale transitions (`0.0–1.0` to `0–1000`) require idempotent `ALTER TABLE` and row-rescaling guards inside `_init_db()` and `_load_game()` so existing player saves do not break on upgrade.
- Concurrent multi-writer web deployment is out of scope without swapping the persistence adapter behind `VeilGameEngine`.
