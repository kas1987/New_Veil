# District: The Hollow

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: VEIL-003 — Emotional depth unlocks truth.
> Canon ref: MEM-001 — Memory affects identity and world state. (per Immutable Canon — dreams and echoes can reveal hidden truth)

---

```yaml
name: The Hollow
mood: liminal, dreamlike, disorienting
prism_score: 0.5
dq_score: 0.5
unlock_condition: emotional_depth >= 0.75 OR has_seen_dream == true
symbolic_objects:
  - void mirror
  - thread unspooling into darkness
  - a door with no wall
hidden_layer: >
  The Hollow IS The Veil thinned to near-transparency.
  The Sisters meet here. The Unbound live here between walks.
  A visitor who reaches it intact stands at the actual threshold of truth.
faction_presence:
  only: The Unbound
```

---

The Hollow is not a place that was built. It is what remains when the structure of everything else recedes far enough.

Visitors who reach The Hollow — through sufficient emotional depth or through the destabilizing passage of a dream — find something that resembles a city the way a reflection resembles a face. Buildings appear, but their walls are suggestions. Streets are present but loop in ways that resist mapping. The light has no identifiable source. Sound arrives at a slight delay, as if the air here processes things more carefully.

This is not a failure of reality. It is reality without the scaffolding The Veil normally erects to make it bearable.

The Unbound live here between their appearances elsewhere. The Threadwatcher can be found at a threshold that appears to be a door — carved frame, intact hinges — standing in open air with no wall on either side. The door opens onto something. Visitors who have earned enough depth to be here have also, generally, earned the ability to look through it without losing themselves.

The void mirror at The Hollow's center does not show the visitor's reflection. It shows the version of the visitor that would have arrived if they had taken different turns — better turns, worse turns, turns that led to the same place through different costs. This is not meant to be comforting. It is meant to be true.

**On the Sisters:** The Sisters are core archetypal forces (per Immutable Canon). The Hollow is where they convene. They are not agents in the conventional sense — they predate the town's current structure. Their presence here is the reason The Hollow has equal Prism and Dark Quasar scores: they hold both, and the district reflects their balance.

**On depth:** The Hollow cannot be reached below `emotional_depth 0.75` unless a dream event has fired. This is a hard threshold, not a suggestion. A visitor who arrives below threshold — through exploit or error — should find the district partially legible at best, deeply disorienting at minimum. The world does not punish them, but it does not accommodate them either.

---

## Discoveries

- The Hollow must NOT appear on any map or district list visible to `emotional_depth < 0.75` visitors without a dream flag. Its existence is itself gated knowledge.
- The void mirror mechanic requires a "counterfactual player state" system — the mirror shows an alternate version. This is a runtime feature, not a static lore element. Flag for agent/runtime workers.
- The Sisters are referenced but not yet defined as agents or archetypes. This is intentional — their definition should be its own task. Do not let other workers speculatively assign them names or attributes.
- The Threadwatcher (Unbound representative) spawns once per arc in The Hollow specifically. Runtime must enforce single-instance spawn with arc-reset.
- The Hollow's equal prism/dq scores (0.5/0.5) signal its role as synthesis, not as neutrality — it contains both fully, not partially. Documentation and runtime systems should not treat it as a "moderate" district.
