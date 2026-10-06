# Security & Containment Notes

This engine simulates emotional dynamics for a fictional game. It is not a clinical or behavioral-prediction tool. The notes below cover containment of the *simulation*, not real-world social risk.

## Boundaries

- **No PII.** Configs reference fictional characters only (Mira, Shadow, Elias, Lyra, Player, AllyA/B, RivalC).
- **No external I/O.** The runner reads `configs/` and writes `results/`. No network calls, no telemetry.
- **No model-driven content.** Engine is deterministic given seed; persona dialog is the *consumer's* responsibility, not the engine's.
- **JSON-only persona authoring.** Adding a new Sister cannot escalate code paths — it only registers entries in `personas.json` consumed by L1/L2/L5. New `effect` strings in `override_rules` that aren't recognized in `narrative_overrides.pre_apply` are silently ignored.

## Containment of Manipulative Patterns

The engine deliberately models manipulation tactics (deception, mirror, punish_optimization). Two safeguards keep the system honest:

1. **Win condition is fixed in code** (`models.CoreState.win_condition`). It cannot be loosened from JSON.
2. **No "easy win" path.** Dark Quasar applies gravity drag once Trust crosses `trust_quasar_threshold`, ensuring high-Trust states stay narratively earned.

## Threat Model (Game-Internal)

| Risk                                    | Mitigation                                      |
|-----------------------------------------|-------------------------------------------------|
| Player optimizes a single signal to win | L5 `punish_optimization` rule (Elias)           |
| Player exploits low-noise Veil window   | `VeilStateMachine.schedule` rotates states      |
| Persona JSON typo silently corrupts run | `filter_signal` returns `{}` on unknown signal  |

## Out of Scope

- Adversarial use against real people. The model is calibrated to game-relevant ratios (5:1 Magic Ratio territory) and is not validated for clinical inference.
