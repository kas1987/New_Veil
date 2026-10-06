# Symbolic Objects

Objects in Veil Town are not props. They are perceptual nodes — the town's nervous system made tangible. When a player interacts with a symbolic object, the interaction registers in The Veil as a symbolic event, which may trigger dreams, echoes, depth adjustments, or district state changes. Objects carry two meanings simultaneously: a Prism meaning (accessible to all players) and a DQ meaning (only surfaced when depth thresholds are met). Both meanings are true. The DQ meaning is more true. (Canon: VEIL-001, VEIL-004)

---

## Catalog

| Object | Prism Meaning | DQ Meaning | Trigger |
|--------|--------------|------------|---------|
| Mirror | Reflection, self-knowledge | The self you hide | Reveals current depth level as symbolic imagery — not a number, an image |
| Key | Access, possibility | What you're locked out of | Unlocks a district transition if `depth >= district.depth_threshold` |
| Ash | Memory turned to dust | Transformation residue | Fires a `memory_echo` dream on next rest phase |
| Thread | Connection, guidance | The leash | Reveals the player's dominant relationship with a specific agent |
| Lantern | Warmth, safety | What casts the shadow | Marks a Prism surface node; DQ players see the shadow the lantern makes, not the light |
| Void door | The threshold | What's on the other side | Only rendered when `emotional_depth > 0.75`; before that threshold, the door does not appear |

---

## Object Interaction and the Event Engine

The event engine treats symbolic object interactions as typed events with a `symbolic_object` field. When a player touches, examines, or activates a symbolic object, the engine fires an `object_event` with the object type, the player's current depth, and the district context. The engine resolves two outputs from this event: a **surface response** (Prism layer, always delivered) and a **depth response** (DQ layer, delivered only if depth threshold is met).

The engine must maintain a `symbolic_object_registry` — a flat lookup table mapping `object_type` → `prism_trigger`, `dq_trigger`, `depth_required`, and `echo_eligible: bool`. This registry is the contract between the lore layer and the runtime. Lore authors update the registry when new object types are introduced; the event engine never hardcodes object behavior — it always queries the registry.

Objects tagged `echo_eligible: true` (currently: Ash, Thread, Mirror) schedule an echo event against the memory record most recently associated with that object type in the player's session. Objects tagged `echo_eligible: false` produce immediate state effects only.

The Mirror is a special case: its DQ interaction does not produce an echo. It produces a depth report rendered as imagery — the engine calls a `mirror_report()` function that translates the current `emotional_depth` float into a symbolic description string. This string is not a number. Players should never see their depth score directly. (Canon: VEIL-003)

---

## Canon Citations

| Canon Entry | Implemented By |
|-------------|---------------|
| VEIL-001 (Prism/DQ duality) | Every object carries both layers; DQ meaning gated by depth |
| VEIL-003 (Depth unlocks truth) | Object DQ responses gated by `emotional_depth` threshold |
| VEIL-004 (Symbolic interaction reveals truth) | Object events logged as Veil perceptions; trigger echo and dream chains |
| MEM-001 (Memory shapes world state) | Ash and Thread echoes read from memory records |

---

## Discoveries

- The `symbolic_object_registry` should be a JSON file at `12_metaphysics/symbolic_object_registry.json`, read by the event engine at boot. This allows lore authors to add new objects without touching Python code.
- The void door's conditional render requires the event engine to pass `depth` to the district renderer before object lists are assembled. The renderer must filter `void_door` from the object list when `depth < 0.75` — it should not appear as a locked object, it should simply not appear.
- `mirror_report()` needs a mapping table of depth ranges → symbolic imagery strings. This mapping belongs in the metaphysics layer, not the event engine. Suggest `12_metaphysics/mirror_depth_map.json`.
- The `echo_eligible` flag on object interactions creates a dependency between ECHO_SYSTEM.md and this catalog — the event engine must import both systems' contracts. Wave 3A should initialize these as sibling modules under a `metaphysics/` package.
- No object should directly communicate a numerical value to any UI layer. All Veil metrics (depth, resonance, corruption) must be translated to symbolic imagery before rendering. This is a rendering contract, not an optional UX choice.
