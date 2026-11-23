---
status: accepted
---

# Zero-Drift Dual-Layer Inspect Verb and Two-Beat District Closure

Symbolic objects (`lantern`, `mirror`, `wall_of_the_unseen_gate`, `thread`, `key`) are interacted with via a dedicated `Inspect` verb in `engine.py` that does not trigger idle Veil drift (`_tick_drift`). Inspecting below an object's `depth_reveal_threshold` renders its `prism_description` and logs `inspected:<id>:prism` (`+0.0` Resonance); inspecting at or above threshold renders `dq_description`, logs `inspected:<id>:dq` in `narrative_beats`, grants a one-time `+5.0` Resonance insight (exempt from per-NPC soft-taper), and unlocks NPC callback references. District 1 (Caetherra) closes narratively through a two-beat arc rather than a mandatory combat or trial gate: (1) the Greeter's reversible False Comfort offer (`Resonance >= 500`, logging `false_comfort_accepted` or `false_comfort_declined`), and (2) inspecting `wall_of_the_unseen_gate` at the Listening Wall (`>= 550`, `storm`/`quasar_active`) plus speaking with Mira in `miras_garden` (`>= 650`, `>= 5` turns), firing `caetherra_awakened` while preserving Mira's Canon #15 unresolved tension.

## Considered Options

- **Dialogue-only symbolic objects or drift-penalized inspection:** Keeps objects abstract in prose or punishes attentive exploration with idle Veil decay.
- **Purely numeric district exit or mandatory boss/resonance trial:** Either leaves District 1 without a narrative payoff or forces a railroaded combat/trial climax against Caetherra's contemplative tone.

## Consequences

- Attentive players are rewarded for revisiting familiar objects at higher Resonance (`+25.0` max across Caetherra's five objects, preserving the ~10-hour district pacing).
- `Inspect` and `narrative_beats` establish a reusable district-closure pattern for Stillward, Ashveil, and future districts without touching `10_canon/`.
- `engine.py`, session types, and the UI must expose an explicit `Inspect` action alongside `Talk` and `Travel`.
