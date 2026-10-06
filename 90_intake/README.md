# Intake (`90_intake`)

Local-only staging for selective copies from legacy sources. **Bucket contents are gitignored** and must not be pushed to the public repo.

| Bucket | Source |
|--------|--------|
| `from_the_veil/` | clone of `kas1987/The-Veil` |
| `from_viel_small_town/` | clone of `kas1987/Viel-Small-Town` |
| `from_veil_core/` | local production package |
| `from_center_mass/` | local docs / thin game tree |
| `from_zelex_pack/` | local sigil pack |

1. Copy [`sources.example.json`](sources.example.json) → `sources.json` (gitignored).  
2. Fill local paths.  
3. Run `../scripts/intake_copy.ps1`.  
4. Promote keepers into numbered planes via PR.

Process: [`../JOIN_FROM.md`](../JOIN_FROM.md)
