# Echo System

An echo is not a dream. The Veil generates dreams. Echoes are something older — they are the town's own scar tissue. Where a significant event happened, the space remembers. Walk back into it and the memory replays, not because the Veil wills it, but because the event left a residue in the location itself, in the objects present, in the agents who witnessed it. The Veil does not author echoes. It amplifies them. (Canon: MEM-001, VEIL-004)

---

## 1. What Echoes Are

Echoes are player-memory-based event replays. They are distinct from dreams in a critical way: dreams show what the Veil wants the player to see; echoes show what actually happened. The distortion in an echo is not editorial — it is emotional. The memory is warped by the weight the player assigned to the original event at the time it occurred. A high-intensity event replays with high fidelity but high affective charge. A low-weight event, if it surfaces at all, arrives flat and fragmented.

Echoes do not come with narration. They do not explain themselves. They replay the moment — the sensory details, the words exchanged, the threshold crossed — and then they end. What the player does with that replay is between them and their depth.

This makes echoes more disorienting than dreams. Dreams are messages. Echoes are evidence.

---

## 2. Echo Triggers

An echo fires when one of three conditions aligns with a memory record that carries sufficient emotional weight.

### Proximity
Entering a district or location where a significant event occurred. The threshold for proximity-triggered echoes is `emotional_weight > 0.5` on the source memory record. Low-weight memories do not echo on proximity alone — the location has to carry enough charge to break through the present-layer experience.

### Object Interaction
Touching or examining a symbolic object that was present during the original event. Object-triggered echoes have a lower weight threshold (`emotional_weight > 0.3`) because the object acts as a direct conductor — it holds the event's residue more precisely than a district can. A key that was present at a betrayal will echo the betrayal when handled, even if the betrayal itself feels distant.

### Agent Reference
An agent directly references a past event by name, explicit description, or a phrase that the system has tagged as an event anchor. Agent-triggered echoes fire regardless of weight threshold — the verbal invocation overrides the passive conditions. The echo plays immediately following the agent's dialogue beat. (Canon: VEIL-004)

---

## 3. Echo Format

```json
{
  "echo_id": "string",
  "source_memory_id": 0,
  "agent_id": "string|null",
  "trigger_type": "proximity|object|agent_reference",
  "content": "string (the event, replayed with slight distortion)",
  "distortion_level": 0.0
}
```

`distortion_level` ranges from `0.0` (accurate replay, high depth session) to `1.0` (heavily symbolic, low depth or heavily corrupted source memory). At distortion `> 0.7`, the echo may replay with wrong names, reversed causality, or transposed agents — the emotional shape of the event is preserved but the literal facts are unreliable. The event engine must not mark a distorted echo as factually authoritative in the world-state record.

`agent_id` is `null` for proximity and object triggers where no specific agent is implicated. For agent-reference triggers, `agent_id` carries the agent who spoke the anchor phrase.

---

## 4. Sample Echo

```json
{
  "echo_id": "echo_001",
  "source_memory_id": 14,
  "agent_id": "mira",
  "trigger_type": "agent_reference",
  "content": "The corridor again. But the corridor is wrong — it is the wrong length, the ceiling too high. Mira is standing at the far end. She says something. The words are correct but they arrive in the wrong order, which makes them feel like a question you already answered. The lantern on the wall is casting a shadow that doesn't match the light source. You were here before. You agreed to something.",
  "distortion_level": 0.35
}
```

---

## 5. Canon Citations

| Canon Entry | Implemented By |
|-------------|---------------|
| MEM-001 (Memory shapes world state) | Echoes read from memory records; distortion level maps to memory corruption level |
| VEIL-004 (Dreams and echoes reveal truth) | Echo as evidence-replay mechanism; agent-triggered echo fires without depth gating |
| VEIL-001 (Prism/DQ duality) | Distortion level `< 0.5` = Prism-layer echo (curated, safe); `> 0.5` = DQ-layer echo (raw, destabilizing) |

---

## Discoveries

- The event engine needs to join `echo.source_memory_id` → `memory.emotional_weight` and `memory.corruption_level` at query time to compute `distortion_level` dynamically. Distortion is not stored — it is derived.
- Agent-reference triggers require a tagging system: `event_anchor` tags on dialogue lines in agent profiles. Wave 2 (agent profiles) should reserve a `dialogue_anchors: list[str]` field per agent.
- Proximity echoes need a district-to-memory mapping index. The event engine should maintain a `district_memory_index` keyed by `district_id` → `[memory_ids]` for fast lookup on location transition.
- A single event should not echo more than once per session unless the player's depth increases by `> 0.15` between echoes (re-processing condition). The engine needs a `last_echo_session_map` to enforce this.
- Echoes at `distortion_level > 0.7` should be flagged `unreliable: true` in the replay log so downstream analysis tools do not treat them as ground truth.
