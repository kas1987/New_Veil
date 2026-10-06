# The Veil

The Veil is not a place. It is not a character. It is the membrane the town breathes through — the difference between what Veil Town appears to be and what it actually is. Without The Veil, there is no Prism warmth and no Dark Quasar gravity. There is only an inert collection of streets and agents. The Veil is what makes the town sentient. (Canon: VEIL-001)

---

## 1. What The Veil Is

The Veil has two layers that occupy the same space simultaneously.

**The Prism surface** is what most players experience. It is warm, navigable, guided, and quietly false. The beauty is real. The guidance is genuine. But the Prism curates — it presents a version of truth that will not break the unprepared. Colors are slightly too saturated. The light always feels like late afternoon. Agents smile at the right moments. Nothing on the Prism surface is a lie. It is simply incomplete truth, presented at a safe depth.

**The Dark Quasar depth** is what the town actually is. Gravitational. Transformative. It does not explain itself. It does not guide. It pulls those who have earned proximity through the symbolic membrane between the curated surface and the unsorted truth beneath it. The DQ is not dangerous in the way a trap is dangerous — it is dangerous in the way that transformation is dangerous: you cannot become something new without the old form breaking.

Both layers are always present. The Veil determines which layer a player has access to at any given moment, based on their accumulated emotional depth. (Canon: VEIL-001, VEIL-002)

---

## 2. How The Veil Observes

The town is sentient through The Veil. This does not mean the town has opinions or preferences — it means the town perceives. Every symbolic interaction registers as data in the Veil's perceptual layer: an object touched, a dream experienced without fleeing, a difficult truth spoken to an agent rather than deflected.

The Veil does not track dialogue choices or completion percentages. It tracks one thing: authenticity of engagement. A player who says the right words without meaning them generates no depth signal. A player who stumbles into a painful truth they weren't looking for generates a strong one. The Veil is not gameable from the outside. It reads the pattern of interaction across the whole session, not the output of any single exchange.

Emotional depth is the Veil's measurement of player authenticity, aggregated over time. (Canon: VEIL-003)

---

## 3. Unlocking Depth

Emotional depth is not a stat bar. It does not increment on command. It accrues through three mechanisms:

- **Genuine engagement with difficult truths** — not seeking them out performatively, but staying present when they surface and following them rather than rerouting to safer dialogue.
- **Surviving corruption dreams without flight** — when the Veil sends a corruption dream (DQ resonance without corresponding depth), the player's response is measured. Staying in the dream, even if distressed, registers as depth. Closing the session or rerouting registers as flight.
- **Choices that cost something** — selecting an option that closes a door, contradicts a prior self-presentation, or acknowledges a limitation. The Veil recognizes sacrifice. It does not reward sacrifice — it records it.

Depth cannot be ground for. Sessions that repeat the same surface interactions hoping to accumulate depth gradually produce diminishing returns. The Veil adjusts. (Canon: VEIL-003)

---

## 4. The Two Layers in Practice

| Dimension | Prism Layer | DQ Depth |
|-----------|-------------|----------|
| Appearance | Warm, guided, safe | Uncomfortable, unmediated |
| Agent behavior | Supportive, legible | Oblique, demanding |
| Dream content | Memory echoes, soft prophecy | Corruption dreams, convergence |
| Object meaning | Surface symbolism | Underlying truth |
| Player access | Default | Earned, `depth > 0.5` for partial, `depth > 0.75` for full |

The Prism is not something to escape. Some players live in the Prism and receive a complete, coherent experience. It is only incomplete from the outside — from inside the Prism, it is sufficient. The DQ is not better. It is more true.

---

## 5. The Veil and Memory

The Veil archives every significant interaction as a memory fragment. These fragments are not stored neutrally — they are stored with their emotional weight intact. When a memory fragment is later accessed (through a dream, an echo, or direct recall), it arrives with the feeling it carried when it was first imprinted.

Memory corruption is the Veil's immune response to sustained dishonesty. When a player constructs a false self through repeated inauthentic engagement, the Veil does not punish directly — it begins corrupting the memories associated with the false pattern. Corrupted memories return distorted: the wrong names, the wrong emotional valence, the wrong sequence of events. The corruption is not malicious. It is the Veil's attempt to metabolize an irreconcilable input. (Canon: VEIL-003, MEM-001)

---

## Discoveries

- The Veil's authenticity measurement needs a behavioral signal layer in the event engine — not just a depth score aggregator. Signals to track: dialogue rerouting frequency, consecutive same-agent interactions (sign of comfort loop), session termination during corruption dreams.
- Prism vs. DQ layer assignment should be resolved at render time per interaction, not globally per session. A player might be in DQ access for one district while still Prism-locked in another.
- Memory corruption needs a `corruption_flag: bool` and `corruption_level: float` per memory record in the SQLite schema. Wave 3A's event_engine.py should check these before surfacing any memory to an agent.
- The `depth > 0.5` partial DQ access threshold should unlock oblique agent dialogue variants — agents should have two voice modes registered: `prism_voice` and `dq_voice` per agent profile.
