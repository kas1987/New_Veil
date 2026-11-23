---
status: proposed
---

# Zero-Drift Dual-Layer Inspect Verb and Two-Beat District Closure

Target design for District 1 (Caetherra) closure; implementation follows in dedicated feature PRs (until then, `PlayAction` in `04_runtime/game_api/engine.py` has no `Inspect` verb and `01_districts/caetherra.md` treats the eastern wall and Comfort beats as non-mechanical prose).

Under this design, symbolic objects (`lantern`, `mirror`, `wall_of_the_unseen_gate`, `thread`, `key`) will be interacted with via a dedicated `Inspect` verb in `engine.py` that will not trigger idle Veil drift (`_tick_drift`). Inspecting below an object's `depth_reveal_threshold` will render its `prism_description` and log `inspected:<id>:prism` (`+0.0` Resonance); inspecting at or above threshold will render `dq_description`, log `inspected:<id>:dq` in `narrative_beats`, grant a one-time `+5.0` Resonance insight (exempt from per-NPC soft-taper), and unlock NPC callback references. District 1 (Caetherra) will close narratively through a two-beat arc rather than a mandatory combat or trial gate: (1) the Greeter's reversible False Comfort offer (`Resonance >= 500`, logging `false_comfort_accepted` or `false_comfort_declined`), and (2) inspecting `wall_of_the_unseen_gate` at the Listening Wall (`>= 550`, `storm`/`quasar_active`) plus speaking with Mira in `miras_garden` (`>= 650`, `>= 5` turns), firing `caetherra_awakened` while preserving Mira's Canon #15 unresolved tension.

## Considered Options

- **Dialogue-only symbolic objects or drift-penalized inspection:** Keeps objects abstract in prose or punishes attentive exploration with idle Veil decay.
- **Purely numeric district exit or mandatory boss/resonance trial:** Either leaves District 1 without a narrative payoff or forces a railroaded combat/trial climax against Caetherra's contemplative tone.

## Consequences

- Attentive players are rewarded for revisiting familiar objects at higher Resonance (`+25.0` max across Caetherra's five objects, preserving the ~10-hour district pacing).
- `Inspect` and `narrative_beats` establish a reusable district-closure pattern for Stillward, Ashveil, and future districts without touching `10_canon/`.
- `engine.py`, session types, and the UI must expose an explicit `Inspect` action alongside `Talk` and `Travel`.
