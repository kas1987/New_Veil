# Resonance

Resonance is the first player measure. It is not emotional depth. Emotional depth is not a session rule.

Two definitions follow. The wiki is what the town means. The game is what the session does. When they disagree, the game section is the rule for play, and the wiki must be brought back to it.

## Wiki

Resonance is how thin the Veil has worn for this visitor.

The town is a resonant chamber, like the hollow body of a violin. The visitor is the driving frequency. In the physical sense, resonance is an outside vibration meeting an object's own frequency, so energy crosses a barrier with little resistance. Here, the visitor is not solving the town. They are vibrating at a frequency that stops bouncing off the Veil and starts passing through it. The town answers in proportion to that match. It does not hand over a map.

The Prism is still true. It is warm, and it is incomplete. Resonance is not a mood, a bond, or a fact learned. A higher resonance opens places, names, and sentences that stay shut for someone the town has barely met. A high resonance is a thinner membrane, not a finished map. The Veil stays past the visitor, past the player, and past anyone building the town.

The town itself is described as a resonance you achieve rather than a place you merely arrive in (`10_canon/LORE_BIBLE.md`). That sentence is this chamber. It does not mean the visitor comes to know the Veil.

### Grace, then pushback

A chamber has an ambient hum. **0.0** is silence: the visitor is no longer in the town's frequency. A session begins at **350.0** on a **0–1000** Town Resonance scale, already audible. That opening is a grace window, not a permanent floor.

Grace holds the membrane at **350.0** for the first **5** accepted talks, or until resonance first reaches **450.0**, whichever comes first. While grace holds, the town does not thicken against the visitor. When grace ends, the Veil pushes back. Speech with no weight, a repeated echo of the town's own words, and time spent not meeting the frequency all thicken the membrane again. The streets can forget a visitor who never tunes in. A new session starts again at **350.0**, with grace.

### Three timescales: conversation, person, town

1. **Single conversation (5–6 turns):** Immediate encounter stance (`hostile → guarded → open → bonded`) responds in 2–6 attuned turns so every exchange feels alive and personal.
2. **Single NPC bond (0–100, ~25 turns):** Each resident carries a personal `npcBond` (`0–100`) modulated by their `personality_weights`. Positive turns add `1.6×` raw posture gain to `npcBond` (and `+10.0` on a breakthrough), while negative turns deduct `1.5×`. Once a single NPC has contributed **`+50.0`** to global Town Resonance, positive Town gains from that NPC soft-taper to **`0.15×`**, while personal `npcBond` keeps growing at full speed.
3. **Whole town and districts (0–1000, ~200–250+ turns / ~8–10 hours):** Deepening Town Resonance from `350.0` to `800.0+` cannot be ground out on one person in the Plaza — it requires building real rapport across 8+ residents, districts, Veil cycles, and Resonance Trials.

### How a person speaks

The town does not score a pile of lore nouns. It scores conversational posture: whether the visitor is listening, asking, or speaking as themselves. A line of secret words with no sentence is static. A brush-off thickens the membrane. Ordinary attention is enough to be met. Vulnerability is what lets the barrier blur.

| Band | How the talk feels | What the town does |
|---|---|---|
| 0.0–349.99 | Draining. Small talk that dies, a brush-off, a command, talking at someone. | The visitor is static. People pull back. Play thins. |
| 350.0–549.99 | Polite and guarded. Present, civil, nothing risked. | Enough for the main streets. Not enough to see under them. |
| 550.0–749.99 | Engaged. A real question, a reflection of what was just said, an honest observation. | The town leans in. Deeper places open. |
| 750.0–849.99 | Vulnerable. A defense dropped, fear or uncertainty named, an unspoken thing said. | The barrier blurs. A secret that needs the quasar can be reached. |
| 850.0–1000.0 | Intimate. Rare. The words carry weight and nothing is guarded. | The membrane is clear glass. The town answers. This is still not understanding the Veil. |

An Echo Shard and a Vial of Memory Ash remain tuning forks: a fixed strike, **+6.0** and **+10.0**, with no sentence. Below **100.0** they are the blows that can still cross. Time spent not in a real exchange still lets the town seal. A resonant talk, for that seal, is a line that listens, asks, or discloses — not a clipped command.

Ordinary talk thickens or thins the membrane a little at a time. Breaking a person who began closed is different. The damping gives way once, and the chamber surges. After that surge the climb is gradual again. Near awakening the same surge is smaller, so the clear glass stays rare.

### Coupled resonance

A thin membrane is not always enough. Some openings need a second driver: the Veil itself has to be vibrating.

Mira's true name is that case. The visitor's frequency must reach **800.0**, and the veil must be **quasar_active**, before the two waves phase-lock and the name shows. The Listening Wall is the same kind of lock: resonance **550.0**, and the veil in storm or quasar.

A road that lists only a resonance number is a simpler match. The visitor's frequency has met that place's own frequency. No second driver is required. Ashveil at **500.0** is that kind of door.

### What the measure looks like

`12_metaphysics/SYMBOLIC_OBJECTS.md` wants this measure to reach the player as an image. The session still shows the score out of 1000 and a tier name. These are the images that belong behind that number, one per band. They are not on screen yet.

| Band | Range | State of the chamber | Image |
|---|---|---|---|
| Sealed out | 0.0 | Erasure, not death. | The Prism is intact and this visitor is outside its frequency. The session ends. A new session can begin. |
| Critical collapse | 0.01–99.99 | The voice fails to cross. | Typed words drop into static. Roads with no resonance lock twist back to the plaza. People return "…" or the room's own noise. |
| Surface Walker | 100.0–349.99 | The town turns away. | Wind and muffled static. Replies shorten. The depth sentence and opened codex excerpts seal again. |
| First Light | 350.0–549.99 | Sympathetic hum. Grace can still be holding. | Fine ripples when someone speaks. The plaza's depth sentence at **450.0** is the first of these ripples the session shows. Crossing **450.0** also ends grace. |
| Veil Listener | 550.0–749.99 | Standing wave. | A clear, repeating interference. The membrane thins and moves with the town. |
| Quasar Tested | 750.0–849.99 | Phase lock, once the veil is driving. | High amplitude. Edges blur and light bleeds. Mira's name can lock here at **800.0** during quasar, not at the start of the band. |
| Awakened | 850.0–1000.0 | Critical amplitude. | The barrier is nearly transparent and behaves like a vibrating prism, not a wall. Still not a map of the Veil. |

## Game

This is the rule for play, implemented deterministically with 1:1 parity across `04_runtime/game_api/resonance_evaluator.py` (authoritative engine) and `07_ui/game_client/src/lib/resonanceEvaluator.ts` (client sensory cue & calibration suite).

Resonance is one number on the player, from **0.0** to **1000.0**, stored to two decimals for exact amplification and taper math.

- A new session starts at **350.0**, with grace.
- Grace is the first **5** accepted talks, or the moment resonance first reaches **450.0**, whichever comes first.
- While grace holds, resonance cannot fall below **350.0**.
- After grace, shallow speech, repetition, and veil drift lower it toward **0.0**.
- At **0.0** the session ends. The visitor is sealed out. A new session starts at **350.0** with grace again.

Places, codex excerpts, item text, and Mira's true name read this number. They do not read `emotional_depth`. The session still copies resonance into that column on a talk. Nothing in play reads the copy.

### What a talk does

An accepted talk is a non-empty line to someone in the scene or in the party. An empty line or an absent person changes nothing.

The positive pieces, modulated by the NPC's `personality_weights` (default `1.0` each) before the cap:

- **Mirroring, +0.6 × `w.mirror`.** The line contains at least one word from the NPC's immediately previous reply. The word is not a stopword and it is at least three letters.
- **Open question, +0.5 × `w.inquiry`.** The line has `?`, or starts with `how`, `why`, `what do you`, `tell me about`, or `i wonder`.
- **Interiority, +0.6 × `w.interiority`.** The line discloses first-person vulnerability (`i feel`, `i remember`, `i'm afraid`, `i am afraid`, `i don't know`, `i do not know`, `i wonder`, etc.).
- **A thematic word inside a sentence, +0.6 × `w.thematic`.** One distinct non-fatigued word from veil, quasar, prism, truth, memory, shadow, dream, trust, fear, why inside a sentence of at least 4 words. Interiority and this thematic signal together cap at **1.2**.
- **Unhurried, +0.3 × `w.cadence`.** The line is longer than 45 characters and it is not friction.

A keyword dump does not get the thematic mark. A dump is a line whose content words are at least 60% thematic lexicon words (with at least two thematic words).

The positive sum is capped at **+2.5**. Friction, when it applies, replaces that sum. It does not add on top of a gain.

Friction replaces that sum (never soft-tapered):
- **Hostile dismissal, −1.8** (or **−3.0** Trust Rupture when breaking an `open` or `bonded` bond). Under `quasar_active`, negative penalties on `>= 600.0` or `open`/`bonded` stances are amplified by **1.25×** (`−2.25` / `−3.75`).
- **Command, repeat, or keyword dump, −1.2.** (`give`, `open`, `unlock`, `go`, `leave`, `show me`, `tell me the`, exact repeated player line, or thematic dump).
- **Terse or filler without mirroring, −0.8.** Line under 15 characters or filler word when not echoing the NPC's last reply. A short echo such as "What wall?" keeps its gain.

### Per-NPC Bond & Soft Taper

Each NPC tracks `npcBond` (`0.0–100.0`) and `townContribution` (`0.0+`):
- `npcBond` updates from the **pre-taper** posture delta: breakthrough adds **`+10.0`**, positive non-breakthrough turns add **`1.6×`** delta (~25 good turns to reach `100.0`), and friction deducts **`1.5×`** delta.
- Positive global Town Resonance gains from one NPC pay in full up to **`+50.0` `townContribution`**, then soft-taper to **`0.15×`** (so befriending more residents across Veil Town and nearby settlements is necessary to reach higher bands).

### Breakthrough surges

Numbers for this section live in `resonance_talk` inside `14_psychometrics/attributes.json`. A normal talk caps at **+2.5**. One resolving turn may add a **+3.5** breakthrough bonus on top of that talk's positive sum, then stop at a ceiling of **+6.0**. At resonance **800.0** or higher, before the line is scored, that ceiling is **+4.0**. The bonus is added only when the positive sum is in play. Friction replaces the sum and blocks the bonus on that turn.

`resonance_evaluator.py` and `resonanceEvaluator.ts` both apply this section, verified against the shared corpus `14_psychometrics/calibration_corpus.json`.

Each NPC carries an encounter stance for the session: `hostile`, `guarded`, `open`, or `bonded`. The character record may set `encounter_stance`. With no field, the stance is `guarded`.

An attuned line is a non-friction line whose pre-taper gain, before any bonus, is at least **1.1**. Consecutive attuned lines move the stance one step: hostile to guarded, guarded to open, open to bonded. Friction resets that streak. From guarded, friction returns the stance to hostile.

- **Saving face.** The first attuned line to someone `hostile` moves them to `guarded`. The gain stays inside the **+2.5** cap.
- **Affective reversal.** Someone who began the session `hostile`, and who has spent at least **2** talks in hostile or guarded, pays the **+3.5** bonus on the turn the stance becomes `bonded`. That person's breakthrough is spent. Later talks with them use the **+2.5** cap.
- **Integrative synthesis.** Interiority plus a token from a revealed item depth line, or from an open codex title (`min_resonance >= 450.0`), pays the same bonus once for that person. A reversal and a synthesis do not both pay.

Using an item adds that item's `resonance_delta` when it has one. An Echo Shard adds **+6.0**. A Vial of Memory Ash adds **+10.0**. A key item cannot be used. These strikes still apply under **100.0**, where speech is failing.

Winning a trial adds the `resonance_delta` on the chosen reward (`8.0–20.0`). A loss does not. A trial already won does not run again.

### What lowers it

After grace, the losses above are kept. They are not clamped back to **350.0**.

A resonant talk is an accepted line that is not friction and that scores mirroring, an open question, or at least one vulnerability mark. Travel, a veil shift, a purchase, a use, a trial, and a party change each add one to a drift count. Save, load, and a portrait binding do not. On every third such action the count returns to zero and resonance falls **0.5**, or **1.0** if the veil is **storm**. A resonant talk sets the count to zero and does not tick drift.

### Below the starting line

From **349.99** down to **100.0**, people stop offering context. Replies are short. They look past the visitor. The plaza depth sentence and any codex excerpt that had opened seal again. The two rich prompts ("Ask about the Veil", "Probe deeper truth") are gone. What remains are plain queries.

From **99.99** down to **0.01**, the visitor's own line degrades in the log. Words drop out. Roads that list no `min_resonance` still spend the action and return the visitor to the plaza. People do not answer. The log shows "…" or a line about the room. An Echo Shard or Memory Ash can still raise resonance.

At **0.0** the session ends. No death screen. The town's frequency has closed.

### What it opens

Travel uses the higher `min_resonance` on the place and on its settlement. Roads with no such number ignore resonance. Other locks, such as a required item or the veil state, still apply after the resonance check.

The plaza shows its depth sentence at **450.0**.

Codex excerpts open at the `min_resonance` on that entry. The Dark Quasar entry opens at **600.0**.

An item shows its depth text once resonance reaches that item's `depth_reveal_threshold`.

Mira's true name is shown at resonance **800.0**, and only while the veil is **quasar_active**.

One ending flag is resonance at or above **800.0**. That flag is a checklist the builders can close. It is not a claim that anyone understood the Veil.

### Tier names

The client names bands from `14_psychometrics/attributes.json`. A tier is a label for a range. It does not open a road. Roads open from the place's own lock.

| Name | From | A new session |
|---|---|---|
| Surface Walker | 0.0 | The town has turned away, or the visitor is sealed out |
| First Light | 350.0 | Polite, guarded contact. A new session starts here |
| Veil Listener | 550.0 | Engaged. Listening Wall's resonance is met. The veil must still be storm or quasar |
| Quasar Tested | 750.0 | Vulnerable. The Hollow's resonance is met. The road and its other locks still apply |
| Awakened | 850.0 | Intimate. Past the 800.0 true-name number. The name still needs quasar_active |

### Shown on screen

The HUD displays `resonance / 1000` alongside the tier name and a resonant core indicator. At **850.0** and above it is a crisp prismatic ring. At **350.0** it is a slow hazy ripple. At **100.0** it is a sputtering ember.

A locked road shows two waves, not two numbers. The road's wave is the `min_resonance` it demands. The visitor's wave is their current resonance. The road's wave is tighter and brighter. The visitor's is slower and dimmer. The barrier repels the visitor's wave. Both the gap and the direction of it are visible.

Cues to build, so a change is felt without printing the delta:

| Trigger | Delta | Image | Sound |
|---|---|---|---|
| Mirroring the last reply | +0.6 × `w.mirror` | The echoed word holds a faint ripple in the log | A soft harmonic, close to the voice just heard |
| An open question | +0.5 × `w.inquiry` | The input edge lifts, as if the line is still waiting | A short rising tone |
| Interiority or a thematic word in a real sentence | +0.6 each × weight, at most 1.2 | That phrase splits prismatically, with a short vapor ripple | A crystalline overtone, a little higher for the second mark |
| Line longer than 45 characters, and not friction | +0.3 × `w.cadence` | The input edge smokes and keeps a slow drift after the line is sent | A warm sub-bass for about 1.5 seconds |
| Positive gain hits the cap | +2.5 (or `0.15×` tapered) | The frame flares cyan and amber, and the inner mask opens for a moment | A full chord, like a glass singing |
| Friction: terse, filler, command, dump, or hostile dismissal | −0.8 to −3.0 | The line goes muddy grey and falls like ash (violet shock on Trust Rupture) | A dull thud, a string muted with the palm |
| Drift | −0.5 or −1.0 | Smoke pulls inward. The corners of the view close slightly | A short intake, or wind sealing a door |
| Saving face, hostile to guarded | no extra delta | The other person's line stops ringing. The membrane steadies | The muted string releases |
| Breakthrough, reversal or synthesis | +3.5 inside the +6.0 ceiling, or the +4.0 ceiling at 800.0 and above | The damping ring cracks. The core flares once | One chord, wider than the ordinary cap |

The client today shows the percent, the tier name, the gain after a talk, and both numbers on a locked road. Those stay until this layer replaces them.
