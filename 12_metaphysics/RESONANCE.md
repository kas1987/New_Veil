# Resonance

Resonance is the first player measure. It is not emotional depth. Emotional depth is not a session rule.

Two definitions follow. The wiki is what the town means. The game is what the session does. When they disagree, the game section is the rule for play, and the wiki must be brought back to it.

## Wiki

Resonance is how thin the Veil has worn for this visitor.

The town is a resonant chamber, like the hollow body of a violin. The visitor is the driving frequency. In the physical sense, resonance is an outside vibration meeting an object's own frequency, so energy crosses a barrier with little resistance. Here, the visitor is not solving the town. They are vibrating at a frequency that stops bouncing off the Veil and starts passing through it. The town answers in proportion to that match. It does not hand over a map.

The Prism is still true. It is warm, and it is incomplete. Resonance is not a mood, a bond, or a fact learned. A higher resonance opens places, names, and sentences that stay shut for someone the town has barely met. A high resonance is a thinner membrane, not a finished map. The Veil stays past the visitor, past the player, and past anyone building the town.

The town itself is described as a resonance you achieve rather than a place you merely arrive in (`10_canon/LORE_BIBLE.md`). That sentence is this chamber. It does not mean the visitor comes to know the Veil.

### Grace, then pushback

A chamber has an ambient hum. **0.00** is silence: the visitor is no longer in the town's frequency. A session begins at **0.35**, already audible. That opening is a grace window, not a permanent floor.

Grace holds the membrane at **0.35** for the first **5** accepted talks, or until resonance first reaches **0.45**, whichever comes first. While grace holds, the town does not thicken against the visitor. When grace ends, the Veil pushes back. Speech with no weight, a repeated echo of the town's own words, and time spent not meeting the frequency all thicken the membrane again. The streets can forget a visitor who never tunes in. A new session starts again at **0.35**, with grace.

### How a person speaks

The town does not score a pile of lore nouns. It scores conversational posture: whether the visitor is listening, asking, or speaking as themselves. A line of secret words with no sentence is static. A brush-off thickens the membrane. Ordinary attention is enough to be met. Vulnerability is what lets the barrier blur.

| Band | How the talk feels | What the town does |
|---|---|---|
| 0.00–0.34 | Draining. Small talk that dies, a brush-off, a command, talking at someone. | The visitor is static. People pull back. Play thins. |
| 0.35–0.54 | Polite and guarded. Present, civil, nothing risked. | Enough for the main streets. Not enough to see under them. |
| 0.55–0.74 | Engaged. A real question, a reflection of what was just said, an honest observation. | The town leans in. Deeper places open. |
| 0.75–0.84 | Vulnerable. A defense dropped, fear or uncertainty named, an unspoken thing said. | The barrier blurs. A secret that needs the quasar can be reached. |
| 0.85–1.00 | Intimate. Rare. The words carry weight and nothing is guarded. | The membrane is clear glass. The town answers. This is still not understanding the Veil. |

An Echo Shard and a Vial of Memory Ash remain tuning forks: a fixed strike, **0.04** and **0.06**, with no sentence. Below **0.10** they are the blows that can still cross. Time spent not in a real exchange still lets the town seal. A resonant talk, for that seal, is a line that listens, asks, or discloses — not a clipped command.

Ordinary talk thickens or thins the membrane a little at a time. Breaking a person who began closed is different. The damping gives way once, and the chamber surges. After that surge the climb is gradual again. Near awakening the same surge is smaller, so the clear glass stays rare.

### Coupled resonance

A thin membrane is not always enough. Some openings need a second driver: the Veil itself has to be vibrating.

Mira's true name is that case. The visitor's frequency must reach **0.80**, and the veil must be **quasar_active**, before the two waves phase-lock and the name shows. The Listening Wall is the same kind of lock: resonance **0.55**, and the veil in storm or quasar.

A road that lists only a resonance number is a simpler match. The visitor's frequency has met that place's own frequency. No second driver is required. Ashveil at **0.50** is that kind of door.

### What the measure looks like

`12_metaphysics/SYMBOLIC_OBJECTS.md` wants this measure to reach the player as an image. The session still shows a percent and a tier name. These are the images that belong behind that number, one per band. They are not on screen yet.

| Band | Range | State of the chamber | Image |
|---|---|---|---|
| Sealed out | 0.00 | Erasure, not death. | The Prism is intact and this visitor is outside its frequency. The session ends. A new session can begin. |
| Critical collapse | 0.01–0.09 | The voice fails to cross. | Typed words drop into static. Roads with no resonance lock twist back to the plaza. People return "…" or the room's own noise. |
| Surface Walker | 0.10–0.34 | The town turns away. | Wind and muffled static. Replies shorten. The depth sentence and opened codex excerpts seal again. |
| First Light | 0.35–0.54 | Sympathetic hum. Grace can still be holding. | Fine ripples when someone speaks. The plaza's depth sentence at **0.45** is the first of these ripples the session shows. Crossing **0.45** also ends grace. |
| Veil Listener | 0.55–0.74 | Standing wave. | A clear, repeating interference. The membrane thins and moves with the town. |
| Quasar Tested | 0.75–0.84 | Phase lock, once the veil is driving. | High amplitude. Edges blur and light bleeds. Mira's name can lock here at **0.80** during quasar, not at the start of the band. |
| Awakened | 0.85–1.00 | Critical amplitude. | The barrier is nearly transparent and behaves like a vibrating prism, not a wall. Still not a map of the Veil. |

## Game

This is the rule for play, implemented deterministically with 1:1 parity across `04_runtime/game_api/resonance_evaluator.py` (authoritative engine) and `07_ui/game_client/src/lib/resonanceEvaluator.ts` (client sensory cue & calibration suite).

Resonance is one number on the player, from **0.000** to **1.000**, stored to three decimals.

- A new session starts at **0.350**, with grace.
- Grace is the first **5** accepted talks, or the moment resonance first reaches **0.450**, whichever comes first.
- While grace holds, resonance cannot fall below **0.350**.
- After grace, shallow speech, repetition, and veil drift lower it toward **0.000**.
- At **0.000** the session ends. The visitor is sealed out. A new session starts at **0.350** with grace again.

Places, codex excerpts, item text, and Mira's true name read this number. They do not read `emotional_depth`. The session still copies resonance into that column on a talk. Nothing in play reads the copy.

### What a talk does

An accepted talk is a non-empty line to someone in the scene or in the party. An empty line or an absent person changes nothing.

The positive pieces, before the cap:

- **Mirroring, +0.020.** The line contains at least one word from the NPC's immediately previous reply. The word is not a stopword (`the`, `a`, `an`, `and`, `or`, `to`, `of`, `in`, `on`, `for`, `is`, `it`, `that`, `this`, `you`, `i`, `me`, `my`) and it is at least four letters. The first line to that person cannot mirror.
- **Open question, +0.015.** The line has `?`, or it contains `how`, `why`, `what do you`, `tell me about`, or `i wonder`. A line that starts with `give`, `open`, `go`, `take`, `buy`, or `leave`, and has no `?`, does not get this.
- **Interiority, +0.020.** The line contains one of: `i feel`, `i remember`, `i'm afraid`, `i am afraid`, `i don't know`, `i do not know`, `i wonder`.
- **A thematic word inside a sentence, +0.020.** One distinct word from veil, quasar, prism, truth, memory, shadow, dream, trust, fear, why, and the line also has a function word (`i`, `a`, `the`, `to`, `of`, `and`, `that`, `this`, `my`, `me`). Interiority and this thematic signal are the only two vulnerability marks. Together they cap at **0.040**.
- **Unhurried, +0.010.** The line is longer than 45 characters and it is not friction.

A keyword dump does not get the thematic mark. A dump is a line whose content words are more than half lexicon words, or a line with a lexicon word and no function word.

The positive sum is capped at **0.080**. Friction, when it applies, replaces that sum. It does not add on top of a gain.

Friction replaces that sum. It is **−0.030** for a repeated line, a command (`give`, `open`, `unlock`, `go`, `leave`, `show me`, `tell me the`), or a keyword dump (at least two lexicon words, and at least 60% of the line). It is **−0.020** for a line under 15 characters, or a filler line, when that line does not echo a word from the other person's last reply. A short echo such as "What wall?" keeps its gain.

### Breakthrough surges

Numbers for this section live in `resonance_talk` inside `14_psychometrics/attributes.json`. A normal talk still caps at **+0.080**. One resolving turn may add a **+0.070** breakthrough bonus on top of that talk's positive sum, then stop at a ceiling of **+0.150**. At resonance **0.800** or higher, before the line is scored, that ceiling is **+0.115**. The bonus is added only when the positive sum is in play. Friction replaces the sum and blocks the bonus on that turn.

`resonance_evaluator.py` and `resonanceEvaluator.ts` both apply this section. The eval is the client session suite in `resonance.test.ts` and the matching cases in `tests/test_resonance_evaluator.py`.

Each NPC carries an encounter stance for the session: `hostile`, `guarded`, `open`, or `bonded`. The character record may set `encounter_stance`. With no field, the stance is `guarded`. The current roster leaves everyone guarded, so a reversal cannot fire until a character is marked `hostile`.

An attuned line is a non-friction line whose gain, before any bonus, is at least **0.035**. Consecutive attuned lines move the stance one step: hostile to guarded, guarded to open, open to bonded. Friction resets that streak. From guarded, friction returns the stance to hostile.

- **Saving face.** The first attuned line to someone `hostile` moves them to `guarded`. The gain stays inside the **+0.080** cap.
- **Affective reversal.** Someone who began the session `hostile`, and who has spent at least **2** talks in hostile or guarded, pays the **+0.070** bonus on the turn the stance becomes `bonded`. That person's breakthrough is spent. Later talks with them use the **+0.080** cap.
- **Integrative synthesis.** Interiority plus a token from a revealed item depth line, or from an open codex title, pays the same bonus once for that person. A reversal and a synthesis do not both pay.

Using an item adds that item's `resonance_delta` when it has one. An Echo Shard adds **0.040**. A Vial of Memory Ash adds **0.060**. A key item cannot be used. These strikes still apply under **0.100**, where speech is failing.

Winning a trial adds the `resonance_delta` on the chosen reward. A loss does not. A trial already won does not run again.

### What lowers it

After grace, the losses above are kept. They are not clamped back to **0.350**.

A resonant talk is an accepted line that is not friction and that scores mirroring, an open question, or at least one vulnerability mark. Travel, a veil shift, a purchase, a use, a trial, and a party change each add one to a drift count. Save, load, and a portrait binding do not. On every third such action the count returns to zero and resonance falls **0.010**, or **0.020** if the veil is **storm**. A resonant talk sets the count to zero and does not tick drift.

### Below the starting line

From **0.349** down to **0.100**, people stop offering context. Replies are short. They look past the visitor. The plaza depth sentence and any codex excerpt that had opened seal again. The two rich prompts ("Ask about the Veil", "Probe deeper truth") are gone. What remains are plain queries.

From **0.099** down to **0.001**, the visitor's own line degrades in the log. Words drop out. Roads that list no `min_resonance` still spend the action and return the visitor to the plaza. People do not answer. The log shows "…" or a line about the room. An Echo Shard or Memory Ash can still raise resonance.

At **0.000** the session ends. No death screen. The town's frequency has closed.

### What it opens

Travel uses the higher `min_resonance` on the place and on its settlement. Roads with no such number ignore resonance. Other locks, such as a required item or the veil state, still apply after the resonance check.

The plaza shows its depth sentence at **0.45**.

Codex excerpts open at the `min_resonance` on that entry. The Dark Quasar entry opens at **0.60**.

An item shows its depth text once resonance reaches that item's `depth_reveal_threshold`.

Mira's true name is shown at resonance **0.80**, and only while the veil is **quasar_active**.

One ending flag is resonance at or above **0.80**. That flag is a checklist the builders can close. It is not a claim that anyone understood the Veil.

### Tier names

The client names bands from `14_psychometrics/attributes.json`. A tier is a label for a range. It does not open a road. Roads open from the place's own lock.

| Name | From | A new session |
|---|---|---|
| Surface Walker | 0.00 | The town has turned away, or the visitor is sealed out |
| First Light | 0.35 | Polite, guarded contact. A new session starts here |
| Veil Listener | 0.55 | Engaged. Listening Wall's resonance is met. The veil must still be storm or quasar |
| Quasar Tested | 0.75 | Vulnerable. The Hollow's resonance is met. The road and its other locks still apply |
| Awakened | 0.85 | Intimate. Past the 0.80 true-name number. The name still needs quasar_active |

### Shown on screen

The HUD to build is a resonant core: one breathing ring whose amplitude and clarity are this float. At **0.85** and above it is a crisp prismatic ring. At **0.35** it is a slow hazy ripple. At **0.10** it is a sputtering ember. No percent, no tier name in that HUD.

A locked road shows two waves, not two numbers. The road's wave is the `min_resonance` it demands. The visitor's wave is their current resonance. The road's wave is tighter and brighter. The visitor's is slower and dimmer. The barrier repels the visitor's wave. Both the gap and the direction of it are visible.

Cues to build, so a change is felt without printing the delta:

| Trigger | Delta | Image | Sound |
|---|---|---|---|
| Mirroring the last reply | +0.020 | The echoed word holds a faint ripple in the log | A soft harmonic, close to the voice just heard |
| An open question | +0.015 | The input edge lifts, as if the line is still waiting | A short rising tone |
| Interiority or a thematic word in a real sentence | +0.020 each, at most two | That phrase splits prismatically, with a short vapor ripple | A crystalline overtone, a little higher for the second mark |
| Line longer than 45 characters, and not friction | +0.010 | The input edge smokes and keeps a slow drift after the line is sent | A warm sub-bass for about 1.5 seconds |
| Positive gain hits the cap | +0.080 | The frame flares cyan and amber, and the inner mask opens for a moment | A full chord, like a glass singing |
| Friction: terse, filler, command, dump, or the same line again | −0.020 or −0.030 | The line goes muddy grey and falls like ash | A dull thud, a string muted with the palm |
| Drift | −0.010 or −0.020 | Smoke pulls inward. The corners of the view close slightly | A short intake, or wind sealing a door |
| Saving face, hostile to guarded | no extra delta | The other person's line stops ringing. The membrane steadies | The muted string releases |
| Breakthrough, reversal or synthesis | +0.070 inside the +0.150 ceiling, or the +0.115 ceiling at 0.800 and above | The damping ring cracks. The core flares once | One chord, wider than the ordinary cap |

The client today shows the percent, the tier name, the gain after a talk, and both numbers on a locked road. Those stay until this layer replaces them.
