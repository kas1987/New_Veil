---
status: accepted
---

# Three-Timescale Resonance Progression and Per-NPC Soft Taper

Progression is separated into three independent clocks: per-conversation encounter stance (`hostile <-> guarded <-> open <-> bonded` over 5–6 turns), per-character personal bond (`npcBond` 0–100 modulated by `personality_weights` over ~25 turns), and global Town Resonance (0–1000 starting at 350 over ~200+ turns across multiple residents). After a single NPC contributes `+50.0` to Town Resonance, further positive gains from that NPC taper to `0.15x` globally while their personal `npcBond` continues growing at full speed.

## Considered Options

- **Single global float without per-NPC tapering:** Allowed players to grind one friendly NPC in Caetherra Plaza to endgame thresholds (`800+`) within minutes without visiting other districts or characters.
- **Hard 0x cap per NPC:** Punished players who keep talking to a favorite character by cutting off all progression feedback once capped.

## Consequences

- Befriending one resident feels warm within a single sitting while earning town-wide depth genuinely requires engaging diverse people and districts (~8–10 hours projected across Veil Town).
- Friction, Hostile Dismissals, and Trust Ruptures still deduct full global Resonance (and `1.25x` under `quasar_active`) so late betrayal remains costly.
