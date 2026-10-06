# Prism DSSM/Veil Engine

Layered social-physics engine for Prism. **DSSM** = Dynamic Social Systems Modeling — a stocks-and-flows simulator at the intersection of cybernetics, mathematical psychology, attachment theory, and game systems design.

## Architecture

```
L5  Narrative Override   — Sister archetypes bend the rules (Mira/Shadow/Elias/Lyra)
L4  Network Propagation  — Trust/suspicion leak across follower graphs
L3  Veil Field Effects   — Entropy decay, signal corruption, dark-quasar gravity
L2  Attachment Modifier  — Anxious / avoidant / secure multipliers
L1  Persona Filter       — Raw signal name → per-stock delta dict
L0  DSSM Core            — Pure stocks/flows physics (contamination-free)
```

L0 has zero character voice. Every other layer is JSON-configurable and stacks as a transform on top.

## Stocks

| Stock      | Range      | Win Threshold |
|------------|------------|---------------|
| Trust      | [0, 100]   | > 60          |
| Affection  | [0, 100]   | (open)        |
| Suspicion  | [0, 100]   | < 40          |
| Resistance | [0, 100]   | < 35          |

Win condition: all three thresholds met after 50 sessions across positive:negative ratios from 2:1 to 7:1.

## Key Mechanic — Resistance Dissolves Under Trust

```
signal_gain      = 1 - 0.6 * R/100                  # high R chokes positive transfer
R_decay_bonus    = 0.025 * max(0, T - 50)           # high T dissolves R
```

Closure verified empirically: T=28→99, R=72→0 over 120 ticks of supportive signal.

## Run

```bash
pip install -e .[dev]
pytest tests/
python -m prism_dssm.stress_test_runner   # writes results/sweep_summary.json
```

## Tree

```
prism_dssm_veil_engine/
  src/prism_dssm/        # 9 layer modules
  configs/               # 6 JSON configs
  tests/test_smoke.py
  docs/                  # integration / repair / security / whitepaper
  pyproject.toml  manifest.json  AGENTS.md  README.md
```

See `AGENTS.md` for layer ownership and `docs/dssm_whitepaper_seed.md` for the science seed.
