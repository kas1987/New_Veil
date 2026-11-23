---
status: accepted
---

# Numbered ChromaticTrees Planes and Immutable Canon Boundary

The repository is partitioned into numbered ChromaticTrees planes (`00_charter` through `15_voice`) separating charter, districts, systems, memory, runtime, alignment, UI, canon, world, metaphysics, agents, psychometrics, and voice. `10_canon/` is treated as an immutable baseline (never modified without explicit human approval), intake dumps remain local-only under `90_intake/`, and `scripts/check_scaffold.py` enforces layout, secret, and no-local-path hygiene in CI.

## Considered Options

- **Conventional flat `src/` layout:** Scatters narrative canon, alignment rules, and runtime code across shared directories, making it easy for automated agents to accidentally mutate lore constraints while refactoring code.

## Consequences

- Downstream mechanics (`02_systems`, `04_runtime`, `12_metaphysics/RESONANCE.md`) adapt around `10_canon/` rather than rewriting foundational world truths (`calm -> still -> storm -> quasar_active`, `1.25x` Quasar amplification).
- Cross-cutting mechanical updates still coordinate multiple planes deliberately while keeping canon files untouched.
