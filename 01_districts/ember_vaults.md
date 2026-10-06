# District: The Ember Vaults

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: VEIL-003 — Emotional depth unlocks truth.
> Canon ref: MEM-001 — Memory affects identity and world state.

---

```yaml
name: The Ember Vaults
mood: subterranean, weighted, reverent, threatening
prism_score: 0.15
dq_score: 0.90
unlock_condition: emotional_depth >= 0.65 AND has_visited_ashveil == true
symbolic_objects:
  - ember casket
  - the memory anvil
  - sealed vault doors (7)
  - ash-choked stairway
hidden_layer: >
  The Vaults store what the Covenant has burned. Every casket holds a collected
  belief — not destroyed, but archived. The Covenant says they liberate;
  the Vaults say they keep what they take.
faction_presence:
  dominant: Ashen Covenant
  secondary: The Unbound (one sealed vault — Vault Seven — is Threadwatcher territory)
```

---

The Ember Vaults lie beneath Ashveil — not metaphorically, but literally, reached through the ash-choked stairway hidden behind the largest forge. Ashveil burns; the Vaults store what the burning leaves behind. The Covenant calls it transformation. Down here, it looks more like filing.

The district is a vast underground archive organized around a central chamber containing the memory anvil — a massive forge-anvil that does not shape metal. When an Ashen Covenant ritual reaches its conclusion topside, the belief being burned through condenses here, settling into an ember casket the way smoke becomes soot. Each casket is warm to the touch. A visitor with sufficient depth can feel the residual conviction inside, still trying to be believed.

Seven sealed vault doors ring the central chamber. Six are Covenant-controlled, opened only by The Rendered for specific purposes — research, review, or the rare act of returning a burned belief to someone who was not ready to lose it. The seventh vault has no Covenant marking. Its door bears the Threadwatcher's symbol: a single unspooled thread. It has never been recorded as opened. Occasionally, the thread at its frame shifts, as if on the other side someone is pulling gently.

**On the Memory Anvil:** The anvil is where the Covenant's ideology becomes tangible. It is not a tool of destruction — it is an instrument of selection. Beliefs placed on it are not burned; they are tested. Those that survive the test (beliefs held with genuine conviction rather than habit or fear) return reinforced. Those that fail? They become ash, and the ash feeds the Vaults.

**On depth:** The Ember Vaults are inaccessible below `emotional_depth 0.65` and require prior passage through Ashveil (the stairway literally does not exist for visitors who have not crossed the Unseen Gate). At 0.65-0.75, the Vaults feel claustrophobic and ominous — a threat hiding behind ritual. Above 0.75, especially during quasar_active state, a visitor begins to understand what the Covenant actually does, and it is more complicated than either liberation or theft. It is curation. Whether it is kind curation is the question the district refuses to answer.

**Veil state effects:**
- `calm`: The ember caskets glow faintly. Warm but dormant.
- `still`: Caskets dim. The Vaults feel like a library after closing.
- `storm`: Caskets flicker irregularly. Stray memory fragments drift through the air uncontained.
- `quasar_active`: The memory anvil activates. Beliefs surface into view. Vault Seven's thread goes taut.

---

## Discoveries

- The seven vaults should be tracked in runtime as a state machine. Vault Seven's status is independent of Covenant authority.
- Memory fragment exposure in the Vaults should be *curated* — fragments pulled from `replay.jsonl` that match the visitor's emotional depth and current Veil state. Random fragment exposure is for Ashveil; the Vaults know what they hold.
- The Covenant does not admit the Vaults exist to shallow visitors. Their existence below Ashveil is gated knowledge. Runtime must not surface Vault references in any agent communication to a player with `emotional_depth < 0.65`.
- The rendering of The Rendered changes in the Vaults. They become more articulate here. Their silence topside is a choice; down here, among what they have kept, they have things to say.