# Dark Quasar

The Dark Quasar is not evil. It is gravitational truth that cannot be denied.

## Core Mechanic: "No Easy Wins"

In the Veil Town simulation, the Dark Quasar enforces a fundamental law:
**high-trust bonds attract disruption.** When a relationship grows too comfortable,
the Quasar exerts emotional gravity — pulling suspicion higher and affection lower.

This prevents the simulation from collapsing into static positivity. Trust must be
earned continuously, not banked. The deeper you go, the harder truth pulls.

## Pipeline Position (L3c)

The Dark Quasar operates **after** L0 (the core emotional model). It does not distort
incoming signals — it reshapes outcomes. After trust and affection are computed,
the Quasar assesses whether they exceed instability thresholds:

- `trust_instability_threshold` (default: 60.0)
- `affection_instability_threshold` (default: 70.0)

If excess exists, it applies **gravity drag**:
- Suspicion increases by `suspicion_pull × drag_scale`
- Affection decreases by `affection_drag × drag_scale`
- Where `drag_scale = min(1.0, excess / 30.0)`

## Quasar Activation

The Quasar is only active in the `quasar_active` Veil state. During this state:
- Signal spike probability increases (up to 18%)
- Spikes can flip signal polarity (30% chance)
- High affection amplifies negative signals by 25%
- Trust threshold drops to 55 (much easier to trigger)

## Emotional Gravity Table

| Excess | drag_scale | Suspicion + | Affection − |
|--------|-----------|-------------|-------------|
| 5      | 0.17      | +0.025      | −0.009      |
| 10     | 0.33      | +0.050      | −0.017      |
| 20     | 0.67      | +0.100      | −0.034      |
| 30+    | 1.00      | +0.150      | −0.050      |

## Lore Implication

The Dark Quasar is why surface dwellers in Caetherra never see the truth.
Its gravity is tolerable at surface trust levels. But for those who seek depth
— who build genuine bonds — the Quasar tests their certainty.

This is why Mira reveals truth only incrementally. Too much trust too fast triggers
instability. The worthy must endure the Quasar's pull and emerge with **earned**
understanding, not gifted revelation.

## See Also

- `04_runtime/veil_engine/veil_effects.py` — QuasarConfig, DarkQuasar class
- `12_metaphysics/THE_VEIL.md` — The symbolic membrane
- `12_metaphysics/VEIL_STATES.md` — Narrative Veil state descriptions
