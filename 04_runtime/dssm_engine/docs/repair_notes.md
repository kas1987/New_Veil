# Repair Notes

Live log of behavioral fixes. Add an entry when adjusting the engine to repair a divergence between simulated and intended dynamics.

## Format

```
## YYYY-MM-DD — <short title>
**Symptom:** what the trial logs showed
**Root cause:** which layer / parameter / rule
**Fix:** the change
**Verification:** which test or sweep cell now passes
```

## Open Watchlist

- **Anxious + Mira deadlock at high suspicion ratios.** If 2:1 ratio leaves Mira stuck above S=70, the `vulnerability_amplify` rule may need a higher floor or `delayed_trust_gain.amount` raised.
- **Shadow `mirror_player` runaway suspicion.** Tit-for-Tat memory amplification can push S to 100 within ~15 sessions on a noisy ratio. If `win_rate` for Shadow drops below 0.2 across all ratios, cap the amplifier at `1.5×` instead of unbounded.
- **Elias `punish_optimization` interacting with Veil noise.** When `signal_noise > 0.20`, the streak counter can reset spuriously. Consider counting valence rather than exact signal name.

## Closed

## 2026-04-26 — Data Science Layer specialists (menu items #2–#5)
**Symptom:** Foundation shipped per-turn JSONL + per-cell aggregates, but the four follow-up specialists from the ranked menu were still deferred: no parameter calibrator, no anomaly detector, no sensitivity sweeper, no trial-level narrative explainer. Diagnosing Mira ratio-sensitivity or Shadow runaway suspicion still required hand-rolled scripts.
**Root cause:** Only foundation (event log + `analytics.summarize`) had been built. The four specialist modules were planned but not yet implemented.
**Fix:**
1. `src/prism_dssm/calibrator.py` — `calibrate(config_dir, *, grid, target_persona, target_metric, target_value, sessions, ratios, seeds)` → `{best, all_results}`. Validates grid keys against `dataclasses.fields(CoreParams)`; score = `abs(metric_value - target)`; runs in-memory and converts trajectories to event-shaped dicts for `analytics.aggregate_cell`. Handles `time_to_trust_60_mean=None` as score=inf.
2. `src/prism_dssm/anomaly.py` — `detect_anomalies(events_path, *, z_threshold=2.0)` → list of `{persona, ratio, seed, anomalous_stocks: [{stock, value, cell_mean, cell_stdev, z_score}]}`. Cells with <3 trials skipped silently; per-stock stdev=0 skipped.
3. `src/prism_dssm/sensitivity.py` — `sensitivity_report(config_dir, *, fields=None, delta_pct=0.10, sessions, ratios, seeds, target_persona)` → ranked-by-abs(sensitivity) report of ±delta_pct sweeps over 11 auto-detected float `CoreParams` fields (decays, baselines, gate, dissolve_k, release_threshold). Handles PEP 563 stringified annotations.
4. `src/prism_dssm/trace_explainer.py` — `explain_trial(events_path, *, persona, seed, ratio)` → `{lines, turning_points, verdict, _meta}` with `format_narrative(result)` renderer. Verdict: `won` if any session meets full win condition; `regressed` if trust crossed 60 then final<60; else `stalled`. Turning points: trust_breakthrough, peak_suspicion, win_achieved, biggest_drop. Filter mismatch → ValueError.
5. All four modules stdlib-only; no changes to L0 dssm_core; no impact on default sweep wall-time.
**Verification:**
- `PYTHONPATH=src python -m pytest tests/` → **19 passed in 0.06s** (added 9: 2 calibrator, 2 anomaly, 2 sensitivity, 3 trace_explainer).
- Disjoint files across the four specialists — no merge conflicts during parallel build.

## 2026-04-26 — Data Science Layer foundation
**Symptom:** No structured per-turn telemetry; sweep emitted only persona×ratio win rates with no per-stock variability, no time-to-trust, no oscillation, no confidence intervals. Hard to diagnose Shadow's runaway suspicion or Mira's ratio-sensitivity without re-running with `record_trajectory` and parsing in-memory dicts.
**Root cause:** Logging hook (`record_trajectory`) was a per-trial in-memory list with no persistence and no schema. No analytics module existed.
**Fix:**
1. New `src/prism_dssm/analytics.py` (stdlib-only): `metrics_for_trajectory`, `aggregate_cell` (per-stock mean ± 95% CI via Student's t), `summarize` (group JSONL by cell), `t_critical(df)` table.
2. `run_trial` gains `record_events`, `events_path`, `run_id` kwargs (all default-off). When on, emits one JSONL row per session with `{run_id, persona, seed, ratio, session, signal, l1_deltas, post_l5pre_deltas, post_l0_state, veil_state, override_fired, network_neighbors_after}`. File handle opened once per trial in try/finally.
3. `sweep` gains `record_events`, `run_id`, `events_dir` kwargs. When on, writes `<events_dir>/<run_id>.jsonl` and embeds `analytics.summarize(...)` under `out["analytics"]`.
4. Determinism preserved: no new RNG draws in the trial path; snapshots are dict copies.
5. Override-fired detection by diffing pre_apply input vs output (no narrative_overrides change).
**Verification:**
- `pytest tests/ -v` → 10 passed (added 4: `test_event_row_schema_stable`, `test_analytics_synthetic_trajectory`, `test_t_critical_values`, `test_sweep_with_events_smoke`).
- Artifacts: `.agents/research/2026-04-26-dssm-data-science-layer.md`, `.agents/plans/2026-04-26-dssm-data-science-layer.md`, `.agents/council/2026-04-26-pre-mortem-dssm-data-science-layer.md`.
- Deferred (menu items #2-5): calibrator, anomaly detector, sensitivity report, trace explainer.

## 2026-04-26 — DSSM layer audit follow-ups
**Symptom:** Six audit findings against newly merged L0–L5 scaffold: L4 unwired, sweep ignored stress-test config, signal-pool catalog mismatch, `vulnerability_amplify` no-op when L1 emits no relevant stocks, dead `cross_*` cross-coupling fields on `CoreParams`, orphan reference configs.
**Root cause:**
- `stress_test_runner.run_trial` never called `network.propagate`.
- `sweep()` hardcoded sessions/ratios/seeds.
- `signal_weights.json` listed `gift`/`withdrawal`/`betrayal` not in runner pools.
- `narrative_overrides.vulnerability_amplify` only multiplied existing positive stocks.
- `CoreParams.cross_pos_to_*` / `cross_neg_to_*` had no consumers.
- `attachment_profiles.json` and `signal_weights.json` weren't marked as reference snapshots of in-code defaults.
**Fix:**
1. Wire L4: added `network`/`focal` kwargs to `run_trial`, capture session-start `pre_snapshot`, call `propagate(...)` after veil advance; `sweep()` passes `cfg.network`.
2. `sweep()` now reads `cfg.stress_test` for sessions/ratios/seeds with explicit-kwarg override.
3. `signal_weights.json` gains `_runtime_pool` block enumerating signals the runner currently draws.
4. `vulnerability_amplify`: when neither trust nor affection were emitted upstream, inject `affection += (factor - 1.0)` against a `1.0` baseline so the rule remains visible.
5. Removed `cross_pos_to_suspicion`, `cross_pos_to_resistance`, `cross_neg_to_trust`, `cross_neg_to_affection` from `CoreParams`.
6. Tagged `attachment_profiles.json` and `signal_weights.json` with `_status: "reference"` + `_consumed_by` keys.
**Verification:**
- `pytest tests/ -v` → 6 passed (added `test_l4_propagation_changes_neighbors`, `test_vulnerability_amplify_injects_when_missing`).
- Audit artifacts: `.agents/research/2026-04-26-dssm-layer-audit.md`, `.agents/plans/2026-04-26-dssm-audit-followups.md`, `.agents/council/2026-04-26-pre-mortem-dssm-audit-followups.md`.
