# District: Ashveil

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: VEIL-003 — Emotional depth unlocks truth.
> Canon ref: MEM-001 — Memory affects identity and world state.

---

```yaml
name: Ashveil
mood: industrial, heavy, transformative
prism_score: 0.2
dq_score: 0.85
unlock_condition: emotional_depth >= 0.5
symbolic_objects:
  - forge fire
  - ash drifts
  - iron keys
  - broken mirrors
hidden_layer: >
  The ash is composed of erased memories. Walking through it exposes fragments —
  recollections that do not belong to the visitor, or ones they believed they had let go.
faction_presence:
  dominant: Ashen Covenant
```

---

Ashveil does not hide. It is simply on the other side of a wall that most visitors do not perceive as having a gate. When the gate appears — when someone has stayed long enough in Caetherra to feel the warmth for what it costs — they find Ashveil adjacent, grey, and unsurprised to see them.

The district runs on forges. The sound is constant: metal on metal, air forced through fire, the low exhalation of bellows that never fully rest. The light here is orange-grey, filtered through particulate. The Covenant does not announce itself — there are no signs, no welcomes. There are workers at the forges who may or may not respond to questions. There are iron keys hanging at intervals with no locks visible near them.

The ash is the district's true text. It settles on everything. A visitor who walks through the ash drifts will begin to experience memory fragments — briefly, non-linearly, without control. Some of these are their own memories in new configurations. Some are fragments of others who passed through before them. The Covenant considers this education. They believe belief held too tightly becomes the material of oppression, and that ash is what remains when a person finally lets something go.

Whether the Covenant is liberating or predatory depends on who enters and what they carry. The district does not decide for them.

**On depth:** Ashveil is inaccessible below `emotional_depth 0.5`. Visitors who reach it at exactly 0.5 experience it as hostile and disorienting. Those who arrive closer to 0.8 find it clarifying — brutal, but legible. The forges burn the same regardless. The question is whether the visitor's self is stable enough to remain themselves while the ash moves through them.

---

## Discoveries

- Ash memory-fragment exposure requires runtime implementation: when a player is in Ashveil, a `memory_fragment_exposure` event should fire probabilistically, surfacing a tagged past event from `06_logs/replay.jsonl`. Fragments should be tagged `echo_eligible: true` at log time.
- Iron keys are a symbolic object without current lock targets — this is intentional. Their meaning should resolve in a later arc. Do not assign them doors prematurely.
- The Covenant's lead agent "The Rendered" operates here. No proper name, title only — established in FACTIONS.md.
