# Dream System

Dreams are symbolic memory events that can alter player resonance, expose hidden lore, or corrupt certainty.

## Dream Event Shape
- trigger
- symbolic payload
- affected memories
- unlock conditions
- alignment risk

## Veil Bypass

Dreams operate **outside** the normal L3a signal pipeline. When a dream fires:
1. The symbolic payload is written directly to memory, bypassing `apply_veil_scalar()`.
2. The dream does NOT trigger Dark Quasar gravity (L3c is suspended during dreams).
3. However, the dream's alignment risk is judged by the normal scorer after the fact.
4. Dreams can corrupt certainty: a high-risk dream may increase suspicion or decrease trust retroactively.

## Dream Triggers

Dreams may fire when:
- The Veil is in `still` or `calm` state (the membrane is stable enough to carry a signal)
- The player has achieved a resonance threshold with an agent
- A memory event references a locked canon anchor (VEIL-004 through VEIL-010)
- The Dark Quasar was recently active (post-quasar dreams reveal what the gravity obscured)

## Integration with the Orchestrator

The Dream System is scheduled for P2 buildout (#20). When implemented, the orchestrator will:
1. Check dream trigger conditions each tick
2. If triggered, generate a symbolic payload via LLM
3. Write directly to `03_memory/events/` bypassing L3a
4. Score alignment post-hoc
5. Mark affected memories with `emotional_tags: ["dream", "bypass"]`
