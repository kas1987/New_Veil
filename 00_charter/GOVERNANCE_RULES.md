# Governance Rules

> Source of truth for Veil Town authority, decision-making, and escalation.

---

## Authority Hierarchy

| Role | Authority Scope | Override Power |
|------|----------------|----------------|
| **Harness** | All layers — governance, validation, EPIC/PDR | Charter-level; cannot be overridden |
| **Lorekeeper** | Canon, lore, world state, narrative arcs | Canon-layer; cannot override Harness |
| **Sentinel** | Alignment, quarantine, safety gates | Alignment-layer; can quarantine any output |
| **Archivist** | Memory, replay, audit trails, session state | Memory-layer; cannot alter canon or alignment |
| **Janitor** | Cleanup, deprecation, schema migration | Infra-layer; cannot alter canon, alignment, or memory content |

---

## Decision Rules

1. **Canon cannot be altered by runtime.** No agent output, no LLM generation, no
   player interaction may modify `10_canon/IMMUTABLE_CANON.md` or `CANON_INDEX.json`.
   Changes to canon follow the `CANON_CHANGE_POLICY.md` process.

2. **Quarantine is authoritative.** If the Sentinel quarantine gate fires, the output
   is blocked regardless of source. There is no override. Quarantined outputs enter
   the review queue in `05_alignment/` and require explicit Auditor release.

3. **Memory is write-once, append-only.** No runtime process may delete or modify
   an existing memory record. Corrections are written as new memories with
   `correction_of: <id>` refs. The original persists in the audit trail.

4. **Agent actions are logged before execution.** Every meaningful agent action
   (LLM call, relationship update, district unlock, dream generation) is logged
   to `06_logs/replay.jsonl` before the downstream effect fires. This ensures
   reconstruction fidelity even on crash.

5. **EPIC/PDR gating applies to all new work.** No feature, lore expansion, or
   runtime change ships without mapping to an active PDR under an active EPIC.
   See `00_harness/EPIC_OPERATING_SYSTEM.md`.

---

## Escalation Protocol

When two authority layers conflict:

```
Harness > Canon > Alignment > Memory > Infra
```

- **Canon vs Alignment**: If canon enforcement and alignment scoring disagree,
  canon wins for hard rules, alignment wins for soft rules.
- **Alignment vs Memory**: If quarantine says block but memory has already persisted,
  quarantine wins — the persisted record is flagged but not deleted (append-only).
- **Memory vs Infra**: If cleanup requires touching memory records, the Janitor
  must file a PDR and get Archivist sign-off before proceeding.

---

## Destructive Action Guardrails

The following actions are **permanently forbidden**:

1. Deleting entries from `replay.jsonl`
2. Modifying `IMMUTABLE_CANON.md`
3. Overwriting a quarantine decision without Auditor review
4. Resetting player emotional depth to zero without session export
5. Removing a district unlock once earned
6. Assigning names to nameless agents (The Rendered, The Threadwatcher, The Witness)
7. Resolving agent arc tensions in default state (Mira's ambivalence must persist
   until the player acts)

---

## Review Authority by Role

- **Lorekeeper** reviews: canon amendments, lore additions, world state changes
- **Sentinel** reviews: alignment threshold adjustments, quarantine releases
- **Archivist** reviews: memory schema changes, session export/import logic
- **Janitor** reviews: deprecation proposals, cleanup migrations, directory restructuring

Each review produces a written finding in `07_review-inbox/`. Reviews that affect
multiple layers require sign-off from all relevant roles.
