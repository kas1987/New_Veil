---
status: accepted
---

# Authored-First Dialogue Packs and Bounded Memory Recall

Caetherra's five residents (`mira`, `solenne`, `greeter`, `witness`, `threadwatcher`) use authored per-NPC dialogue beat packs keyed by three Bond tiers (`stranger: 0-34`, `trusted: 35-74`, `deep: 75-100`) crossed with four Stance families (`reflective/synthesis`, `grounded/neutral`, `friction/hostile`, `quasar/breakthrough`), with 2-3 rotating lines per cell and optional callback lines triggered by fired `narrative_beats`. When local Ollama (`qwen3:8b`) is enabled, it enriches replies under the same stance, bond, memory, and cue contract using the authored pack as voice anchors. Memory recall is bounded to each resident's last five private exchanges with the player, all fired `narrative_beats`, and `shared` memories from another resident only after reaching `npcBond >= 35` (`Trusted`) with that source resident.

## Considered Options

- **LLM-first with minimal offline fallback:** Breaks offline playability and deterministic CI/psychometric testing, and risks voice drift when local models are unavailable.
- **Explicit branching conversation trees (Ink/Yarn-style):** High authoring overhead per NPC and rigid player-choice buttons that conflict with freeform posture-driven conversation.
- **Omniscient town memory or strict NPC isolation:** Omniscient logs bloat local LLM prompts and feel unnatural; strict isolation prevents the town from feeling socially connected as trust grows.

## Consequences

- Offline playtests, pytest, and the psychometric harness remain 100% deterministic while reflecting `npcBond` tiers and world beats.
- Adding a new district NPC requires authoring a compact ~24-line beat pack rather than a sprawling dialogue graph.
- Cross-NPC gossip scales naturally with earned trust without leaking private conversations.
