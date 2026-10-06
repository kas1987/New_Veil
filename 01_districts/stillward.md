# District: The Stillward

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: VEIL-003 — Emotional depth unlocks truth.
> Canon ref: VEIL-004 — The Prism surface is beautiful and sustained against gravity.

---

```yaml
name: The Stillward
mood: serene, deliberate, crystalline, constrained
prism_score: 0.92
dq_score: 0.08
unlock_condition: emotional_depth >= 0.4 AND player_has_lantern == true
symbolic_objects:
  - the stilling bell
  - white thread lattice
  - prayer mirrors
  - the threshold gate
hidden_layer: >
  The Stillward is where the Prism Congregation practices what it preaches.
  The peace here is real. It is also curated — not organic, but maintained.
  Visitors who reach deep enough notice that nothing in the Stillward decays.
  Nothing changes. Nothing is allowed to.
faction_presence:
  dominant: Prism Congregation
  hidden: A single sealed confessional (Ashen Covenant access, used once per generation)
```

---

The Stillward is Caetherra's prayer — made architecture. A monastery-like sanctuary at the town's northern edge, reached through a white-thread lattice gateway that shimmers only during calm and still Veil states. The district is beautiful in a way that does not ask permission: white stone, soft light, the constant low tone of the stilling bell that seems to synchronize the visitor's heartbeat to the district's rhythm.

Prism Congregation wardens maintain the Stillward. They are not guards — they are gardeners of peace. They tend the prayer mirrors that line the cloister walk, each one showing a slightly different reflection of the visitor: calmer, more resolved, more certain. The wardens say the mirrors show who you could become. They do not mention that the mirrors cannot show who you already are.

**On the Stilling Bell:** The bell does not ring in the conventional sense. It resonates — a single, unbroken tone that exists in the space between hearing and feeling. During calm state, it is barely perceptible. During storm, it becomes distinct — a counter-frequency to the Veil's distortion. During quasar_active, the bell *silences*. The Stillward's greatest protection fails at the moment it is most needed, and the district becomes defenseless against gravity.

**On the Threshold Gate:** The Stillward is entered through a threshold gate at its southern edge — a physical doorway that tests the visitor's lantern. Those who received their lantern in Caetherra and merely carried it pass through. Those who used their lantern — who looked at something the light revealed and did not turn away — find the gate wider. The Stillward rewards engagement, not possession.

**On depth:** The Stillward is the most Prism-heavy district in the town, and it shows. At `emotional_depth 0.4-0.55`, it feels like genuine sanctuary. At `0.55-0.7`, the lack of change becomes noticeable — the same flowers bloom in the same arrangement, the same prayers echo at the same hours. Above `0.7`, visitors with sufficient depth begin to perceive the Stillward's hidden truth: it is maintained against entropy through effort. The peace is real, but it costs. Someone is holding this still, and the effort of that holding is The Veil's most impressive and most exhausting performance.

**The Confessional:** Deep beneath the Stillward's cloister, behind a wall that only appears during quasar_active Veil state, is a single sealed confessional. It belongs to the Ashen Covenant. Once per generation, one of the Congregation enters the Stillward, uses the confessional, and tells a truth so heavy the Prism wardens cannot maintain it. The confessional exists because the Congregation and the Covenant were once the same organization, before the schism. This fact is not in any public canon. The Stillward keeps it the way it keeps everything: still.

**Veil state effects:**
- `calm`: The Stillward is at its most beautiful. Everything works as intended.
- `still`: A perceptible waiting quality. The mirrors show fewer variations.
- `storm`: The stilling bell rings loud. The wardens are tense. The peace requires effort.
- `quasar_active`: The bell falls silent. The mirrors shatter one by one. The confessional door appears.

---

## Discoveries

- The Stillward's Prism score (0.92) is the highest of any district. Runtime must model its DQ surface as near-zero while maintaining its hidden confessional as a structural weakness.
- The "prayer mirror" mechanic should be a runtime feature: mirrors show idealized player states. When they shatter during quasar_active, the player sees their actual state — unfiltered.
- The Ashen Covenant confessional is a single-event-per-arc occurrence. It should not fire in every quasar_active transition.
- The threshold gate's lantern test maps to the player having at least one meaningful interaction in Caetherra (lantern received AND used). Runtime must track `lantern_used` as a player flag.
- The Stillward's wardens are not currently agent profiles. They should remain NPC-grade (not full agents) unless a narrative arc requires one to become prominent.