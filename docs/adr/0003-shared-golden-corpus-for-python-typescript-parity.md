---
status: accepted
---

# Shared Golden Corpus for Python–TypeScript Evaluator Parity

The Resonance posture evaluator is implemented in both Python (`04_runtime/game_api/resonance_evaluator.py`) for authoritative persistence and TypeScript (`07_ui/game_client/src/lib/resonanceEvaluator.ts`) for instant sandbox/cue responsiveness, using an explicit half-away-from-zero `round2` helper. Both runtimes execute against the same `14_psychometrics/calibration_corpus.json` vectors in CI under both `pytest` and `vitest`.

## Considered Options

- **Backend-only scoring over HTTP:** Forces an API round-trip for offline client prototyping and couples frontend cue feedback tightly to server availability.
- **Python-to-TS codegen:** Premature build complexity for a single self-contained scoring module.

## Consequences

- Floating-point rounding (`0.375 -> 0.38`) stays bit-identical across Python and V8.
- Any rule or weight change requires updating both modules; missing one immediately fails the shared corpus test in Pytest or Vitest.
