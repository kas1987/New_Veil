# District: Caetherra

> Canon ref: VEIL-001 — The Veil has a Prism surface and Dark Quasar depth.
> Canon ref: MIRA-001 — Mira / Thesmera Locke is the first awakening point for most players.

The player number this district uses is **resonance**. The definition is `12_metaphysics/RESONANCE.md`. It starts at 350.0. Talk, a consumed shard, a won trial, and a first-time Dark Quasar symbolic object inspection (`+5.0`) raise it. Travel locks and the depth line on the plaza read it.

`emotional_depth` is not a Caetherra mechanic. The session copies resonance into a column with that name and never reads the column back. Do not gate this district on it.

---

## What the session does

The session starts in Caetherra Sunlit Plaza. The road here has no lock. Mira is the first person selected. Her greeting is the first line in the feed. Solenne and the Greeter (Halen Vey) are also in the plaza. The Greeter cannot join the party. Caetherra's five residents (`mira`, `solenne`, `greeter`, `witness`, `threadwatcher`) speak from per-NPC beat packs keyed by Bond tier (`stranger`, `trusted`, `deep`), stance family, fired `narrative_beats`, and Trusted (`npcBond >= 35`) shared rumors.

The surface description is always on screen. At resonance **450.0** the client also shows the location's depth sentence: the cobblestones and the counted footsteps.

Players can `Inspect` present symbolic objects (`lantern`, `mirror`, `wall_of_the_unseen_gate`, `thread`, `key`) with zero idle drift. Below each object's `depth_reveal_threshold`, `Inspect` logs `inspected:<id>:prism`; at or above threshold, it reveals `dq_description`, logs `inspected:<id>:dq`, and grants a one-time `+5.0` Resonance insight.

Two hidden places open off the plaza. The thresholds are the ones in `11_world/world_manifest.json`.

| Place | Opens when |
|---|---|
| The Listening Wall | Resonance **550.0**, and the veil is **storm** or **quasar_active** |
| Mira's Garden | Resonance **650.0**, and **turns taken** is at least **5** |

Turns taken increases by one each time the player talks. The garden check uses that counter. It does not count talks with Mira alone, and it does not require her true name.

District closure runs through two recorded narrative beats:
- **False Comfort (`Resonance >= 500.0` at Caetherra Plaza)**: Halen Vey offers a comfortable seat; choosing `accept` or `decline` logs reversible `false_comfort_accepted` / `false_comfort_declined` beats that unlock NPC callbacks.
- **Caetherra Awakened**: Inspecting `wall_of_the_unseen_gate` at Dark Quasar depth on The Listening Wall (`>= 550.0`, `storm` or `quasar_active`) and then speaking with Mira inside Mira's Garden (`>= 650.0`) records `caetherra_awakened`.

Ashveil, east of the plaza, opens at resonance **500.0**. That is a different district.

The lantern is not handed over in the square. It costs 15 Echoes at Lanternwright's Bazaar. Buying it advances The First Light.

---

## Written, not a mechanic yet

These stay in the prose until a session rule exists for them.

- The fountain drain into the Ashen tunnels and warmth underfoot as separate interactable triggers.
- The Echo Corridor. It is not a place in the world manifest.

Mira's central tension stays unresolved in her default state. That is a writing rule for anyone speaking as her, not a travel lock.
