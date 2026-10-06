# District: Caetherra

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: MIRA-001 — Mira / Thesmera Locke is the first awakening point for most players.

---

```yaml
name: Caetherra
mood: warm, deceptively welcoming
prism_score: 0.8
dq_score: 0.3  # hidden beneath surface
unlock_condition: default — always accessible
symbolic_objects:
  - wall_of_the_unseen_gate
  - lantern
  - cobblestones
  - the fountain at the center
hidden_layer: >
  Below the warm surface, the fountain drains into the Ashen tunnels.
  Those with emotional_depth > 0.6 perceive it as warmth underfoot rather than comfort.
faction_presence:
  public: Prism Congregation
  hidden: Ashen Covenant
```

---

Caetherra is the first thing a visitor sees — and for many, the last. It presents as a warm market town under permanent gold light. The cobblestones are even. The fountain at the center runs clean. A lantern is offered at the edge of the square; most visitors accept it without noticing they never asked for it.

The Prism Congregation maintains Caetherra's welcome. They are not performing warmth — it is real. But warmth sustained against a counterpressure is not the same as warmth freely given, and those who stay long enough begin to feel the effort behind it. The cobblestones near the fountain are slightly warm underfoot. In the early morning, when the square empties, the fountain sound changes — something in the drain, something pulling downward.

Thesmera Locke (Mira) is the most common first contact. She lives at the district's threshold in both the literal and symbolic sense — she knows the filter the Congregation runs, and she knows the tunnels beneath the fountain, and she has not decided what to do with either piece of knowledge. Her ambivalence is the district's first real invitation: she will answer direct questions with unexpected honesty if the player earns it.

**On depth:** Visitors with `emotional_depth > 0.6` begin to perceive Caetherra's second register. The fountain's drain becomes visible. The warmth underfoot reads as heat. The Congregation's smiles acquire a slight evaluative quality. Nothing bad happens — the district does not punish depth — but it changes. Caetherra at depth is a more honest, more uncomfortable, more interesting place.

---

## Discoveries

- Caetherra's physical transition to Ashveil occurs at the eastern wall. This wall should carry its own symbolic identifier in runtime (`wall_of_the_unseen_gate`) — it does not appear to have a gate until `emotional_depth >= 0.5`.
- Mira's positioning here (aware of the filter, ambivalent) creates her central tension. Agent workers must not resolve this tension in her default state — her arc is the resolution.
