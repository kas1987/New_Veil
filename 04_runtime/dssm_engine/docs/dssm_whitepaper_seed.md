# DSSM Whitepaper — Seed

> Working title: *Dynamic Social Systems Modeling: A Layered Field-Effect Engine for Narrative Game Worlds*

## 1. Premise

DSSM treats relationships as **stocks** (Trust, Affection, Suspicion, Resistance) governed by **flows** (signal-driven deltas, decay, cross-couplings). It draws from:

- **Cybernetics** (Meadows, *Thinking in Systems*) — bounded stocks, feedback loops, leverage points.
- **Mathematical psychology** — Gottman's 5:1 Magic Ratio as the calibration anchor for win-condition tuning.
- **Social Exchange Theory** (Homans, Blau) — costs/rewards expressed as per-stock deltas.
- **Attachment Theory** (Bowlby, Ainsworth) — anxious / avoidant / secure as multiplier sets on the same physics.
- **Game theory** (Axelrod, *The Evolution of Cooperation*) — Tit-for-Tat with memory as the Shadow archetype's L5 rule.

## 2. The Layered Architecture

L0 is contamination-free physics. Layers L1–L5 are *transforms* that compose without leaking persona, narrative, or chaos into the core. The pipeline is:

```
signal_name → L1 filter → L2 attachment → L3a noise → L5 pre →
              L0 apply  → L3b decay     → L3c quasar  → L5 post → L5 tick
```

This factoring is what makes the engine **add-a-Sister-with-JSON** rather than add-a-Sister-with-a-PR.

## 3. Two Anchor Equations

```
signal_gain   = 1 - resistance_gate * R / 100        # high R chokes positive transfer
R_decay_bonus = trust_dissolve_k  * max(0, T - 50)   # high T dissolves R
```

These two terms close the loop: Trust earned earlier *unlocks* the system to receive more Trust. Without the second, Resistance is a permanent ceiling. Without the first, Trust is a free lunch.

## 4. The "No Easy Wins" Invariant

The Dark Quasar (L3c) applies a gravity drag when Trust crosses a threshold (default 55). This encodes the narrative claim that *high-Trust bonds attract disruption* — a deliberate counterweight to the otherwise positive feedback loop. It keeps the win state earned, not optimized.

## 5. Validation Plan

Per-persona × per-ratio × per-seed sweep (`stress_test_runner.sweep`). The win condition `T > 60 ∧ S < 40 ∧ R < 35` after 50 sessions is the empirical anchor. Calibration target: ratios in [4, 6] should yield non-trivial win rates for secure personas, marginal rates for anxious/avoidant, and effectively zero for adversarial Shadow.

## 6. Open Questions

1. Is the `trust_dissolve_k = 0.025` correctly tuned, or does it make late-game Trust trivially compounding?
2. Should L4 (Network) feed back into L0 within the same session, or only between sessions?
3. Does the Dark Quasar threshold need to be persona-relative rather than absolute?

## 7. Next Steps

- Run the full 120-trial sweep, post `results/sweep_summary.json` to `docs/repair_notes.md`.
- Calibrate L5 rule constants until win-rate curves match designer intuition.
- Promote stable rules from `narrative_overrides.py` into named archetype docs.
