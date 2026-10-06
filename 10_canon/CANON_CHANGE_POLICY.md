# Canon Change Policy

## Immutable Canon

The truths in `IMMUTABLE_CANON.md` and anchors in `CANON_INDEX.json` with
`mutable: false` **cannot be changed** by agents, runtime scripts, or
autonomous processes under any circumstances.

### Amendment Process
The only way to amend immutable canon is through explicit human approval:
1. Submit a canon change proposal to the Lorekeeper
2. Human review and approval required
3. Change must preserve the spirit of the original truth
4. `CANON_INDEX.json` version must be incremented

## Expandable Canon

Canon entries with `mutable: true` (or newly proposed entries) may be
expanded by agents under the following conditions:
1. The expansion does not contradict any immutable canon
2. The expansion is logged with a canon reference
3. The expansion passes alignment scoring (canon_fidelity ≥ 0.75)
4. The expansion is reviewed by the Lorekeeper

### Expandable Categories
- District descriptions and atmosphere
- Agent dialogue examples and emotional maps
- Hidden path descriptions and unlock conditions
- Dream event payloads and symbolic content
- Relationship histories and dyad interactions

## Review Authority

| Change Type | Required Reviewer | Review Gate |
|-------------|-------------------|-------------|
| Immutable canon amendment | Human + Lorekeeper | Full governance review |
| New expandable canon | Lorekeeper | Canon review |
| Agent behavior rules | Sentinel | Safety review |
| Memory schema changes | Auditor | Persistence review |
| UI/rule changes | Cartographer | Design review |
| Veil Engine parameters | Architect | Code review |
| Voice/SSML changes | WhisperTech | Voice review |

## Quarantine

Any output that violates canon, corrupts memory, destabilizes runtime, or
invents major lore without approval is quarantined per the Harness quarantine rule.
