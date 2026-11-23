---
status: proposed
---

# Authored-First Dialogue Packs and Bounded Memory Recall

Target design for District 1 (Caetherra) closure; implementation follows in dedicated feature PRs (until then, `04_runtime/game_api/engine.py` uses the shared fallback reply template noted in `01_districts/caetherra.md`).

Under this design, Caetherra's five residents (`mira`, `solenne`, `greeter`, `witness`, `threadwatcher`) will use authored per-NPC dialogue beat packs keyed by three Bond tiers (`stranger: 0-34`, `trusted: 35-74`, `deep: 75-100`) crossed with four Stance families (`reflective/synthesis`, `grounded/neutral`, `friction/hostile`, `quasar/breakthrough`), with 2-3 rotating lines per cell and optional callback lines triggered by fired `narrative_beats`. When local Ollama (`qwen3:8b`) is enabled, it will enrich replies under the same stance, bond, memory, and cue contract using the authored pack as voice anchors. Memory recall will be bounded to each resident's last five exchanges with the player, all fired `narrative_beats`, and `shared` memories from another resident only after reaching `npcBond >= 35` (`Trusted`) with that source resident.

## Considered Options

- **LLM-first with minimal offline fallback:** Breaks offline playability and deterministic CI/psychometric testing, and risks voice drift when local models are unavailable.
- **Explicit branching conversation trees (Ink/Yarn-style):** High authoring overhead per NPC and rigid player-choice buttons that conflict with freeform posture-driven conversation.
- **Omniscient town memory or strict NPC isolation:** Omniscient logs bloat local LLM prompts and feel unnatural; strict isolation prevents the town from feeling socially connected as trust grows.

## Consequences

- Offline playtests, pytest, and the psychometric harness remain 100% deterministic while reflecting `npcBond` tiers and world beats.
- Adding a new district NPC requires authoring a compact ~24-line beat pack rather than a sprawling dialogue graph.
- Cross-NPC gossip scales naturally with earned trust without leaking private conversations.
