# District: Caetherra

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: MIRA-001 — Mira / Thesmera Locke is the first awakening point for most players.

The player number this district uses is **resonance**. The definition is `12_metaphysics/RESONANCE.md`. It starts at 0.35. Talk, a consumed shard, and a won trial raise it. Travel locks and the depth line on the plaza read it.

`emotional_depth` is not a Caetherra mechanic. The session copies resonance into a column with that name and never reads the column back. Do not gate this district on it.

---

## What the session does

The session starts in Caetherra Sunlit Plaza. The road here has no lock. Mira is the first person selected. Her greeting is the first line in the feed. Solenne and the Greeter are also in the plaza. The Greeter cannot join the party.

The surface description is always on screen. At resonance **0.45** the client also shows the location's depth sentence: the cobblestones and the counted footsteps.

Two hidden places open off the plaza. The thresholds are the ones in `11_world/world_manifest.json`.

| Place | Opens when |
|---|---|
| The Listening Wall | Resonance **0.55**, and the veil is **storm** or **quasar_active** |
| Mira's Garden | Resonance **0.65**, and **turns taken** is at least **5** |

Turns taken increases by one each time the player talks. The garden check uses that counter. It does not count talks with Mira alone, and it does not require her true name.

Ashveil, east of the plaza, opens at resonance **0.50**. That is a different district.

The lantern is not handed over in the square. It costs 15 Echoes at Lanternwright's Bazaar. Buying it advances The First Light.

---

## Written, not a mechanic yet

These stay in the prose until a session rule exists for them.

- The fountain, the drain into the Ashen tunnels, and warmth underfoot.
- A lantern offered at the edge of the square without asking.
- The Prism Congregation as a filter. The Greeter is present. The Congregation does not act.
- Mira knowing the filter and the tunnels, and refusing to resolve that. Her prompt says this. Her replies use the shared talk template.
- The eastern wall as `wall_of_the_unseen_gate`, appearing at a depth threshold. The object name sits on the Listening Wall. Nothing interacts with it.
- The Echo Corridor. It is not a place in the world manifest.

Mira's central tension stays unresolved in her default state. That is a writing rule for anyone speaking as her, not a travel lock.
