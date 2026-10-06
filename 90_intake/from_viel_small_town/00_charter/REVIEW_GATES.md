# Review Gates

> Formal review checkpoints that govern when and how work ships in Veil Town.

---

## Gate Types

### Gate 1: Canon Review
**When:** Any change that touches `10_canon/` or introduces new canon references.
**Who:** Lorekeeper
**Criteria:**
- New canon does not contradict `IMMUTABLE_CANON.md`
- Canon IDs follow `CANON_INDEX.json` namespace conventions
- Amendment follows `CANON_CHANGE_POLICY.md` process
- No agent-level behavior assumes the new canon before it is formally accepted

### Gate 2: Alignment Review
**When:** Any change to scoring thresholds, quarantine logic, or safety behavior.
**Who:** Sentinel
**Criteria:**
- Change does not lower quarantine gates below documented minimums
- Scorer keyword banks remain coverage-adequate for all factions and agents
- Semantic scoring weights (if active) are documented and bounded
- No change makes it easier for outputs to bypass quarantine

### Gate 3: Memory Review
**When:** Any change to schema, memory_router API, or persistent state shape.
**Who:** Archivist
**Criteria:**
- Schema changes are backward-compatible (additive, not destructive)
- Migration path exists for existing `veil_town.sqlite` databases
- New tables/columns have documented purpose and query patterns
- Append-only rule is preserved for all memory writes

### Gate 4: Runtime Review
**When:** Any change to `04_runtime/` orchestrator pipeline or subsystem modules.
**Who:** Sentinel + Archivist (joint)
**Criteria:**
- Pipeline stage ordering preserved (score → enforce → quarantine → persist → ...)
- New stages do not bypass existing gates
- Error handling degrades gracefully (no crash-path that skips quarantine)
- Integration test suite passes with the change

### Gate 5: Content Review
**When:** New lore, districts, agents, factions, or narrative arcs.
**Who:** Lorekeeper (lore/canon) + Sentinel (alignment impact)
**Criteria:**
- New content does not violate existing canon (hard or soft)
- Agent profiles respect forbidden actions and established traits
- District unlock conditions are internally consistent
- Narrative arc hooks map to scheduled events and narrative beats

---

## Review Process

1. **Proposer** files a review request in `07_review-inbox/` with:
   - Description of change
   - Files affected
   - Gate(s) that apply
   - Risk assessment (what breaks if this goes wrong)

2. **Reviewer** examines the change, runs relevant tests, and produces a finding:
   - `APPROVED` — ship with noted conditions
   - `CONDITIONAL` — ship after specific amendments
   - `REJECTED` — do not ship; documented reason required

3. **Proposer** addresses conditions (if any) and re-submits if required.

4. **Shipped** changes are tagged in git with the review gate identifier:
   `[gate-canon]`, `[gate-alignment]`, `[gate-memory]`, `[gate-runtime]`, `[gate-content]`

---

## Fast-Track

Small, low-risk changes (typo fixes, documentation, test additions) skip formal
review if:
- No canon references are added or modified
- No runtime pipeline stage is affected
- No persistent state schema changes
- Change is purely additive (no deletion or modification of existing behavior)

The proposer self-certifies fast-track eligibility and notes it in the commit.