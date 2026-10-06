"""End-to-end smoke test. Boots the merged tree, runs one trial per persona."""

from __future__ import annotations

import json
from pathlib import Path

from prism_dssm import analytics
from prism_dssm.config_loader import load_config_dir
from prism_dssm.dssm_core import apply_deltas, decay_step
from prism_dssm.models import CoreParams, CoreState, OverrideContext
from prism_dssm.narrative_overrides import pre_apply
from prism_dssm.stress_test_runner import ScenarioConfig, run_trial, sweep
from prism_dssm.veil_effects import VeilStateMachine

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"


def test_l0_resistance_dissolves_under_trust():
    state = CoreState(trust=28.0, affection=25.0, suspicion=50.0, resistance=72.0)
    params = CoreParams()
    for _ in range(120):
        apply_deltas(state, {"trust": 6.0, "affection": 3.0}, params)
        decay_step(state, params)
    assert state.trust > 60.0
    assert state.resistance < 35.0


def test_config_loader_boots():
    cfg = load_config_dir(CONFIG_DIR)
    assert {"Mira", "Shadow", "Elias", "Lyra"} <= set(cfg.personas.keys())
    assert len(cfg.veil_states) >= 3
    assert cfg.network is not None
    assert cfg.stress_test["sessions"] == 50


def test_run_trial_per_persona():
    cfg = load_config_dir(CONFIG_DIR)
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    for name, persona in cfg.personas.items():
        machine.tick = 0
        result = run_trial(
            persona,
            ScenarioConfig(sessions=20, pos_to_neg_ratio=5.0, seed=11),
            veil_machine=machine,
        )
        assert result.persona == name
        assert result.sessions == 20
        for k in ("trust", "affection", "suspicion", "resistance"):
            v = result.final_state[k]
            assert 0.0 <= v <= 100.0


def test_sweep_smoke():
    out = sweep(CONFIG_DIR, sessions=10, ratios=(5.0,), seeds=(11,))
    assert out["sessions"] == 10
    assert len(out["cells"]) == 4
    for cell in out["cells"]:
        assert 0.0 <= cell["win_rate"] <= 1.0


def test_l4_propagation_changes_neighbors():
    cfg = load_config_dir(CONFIG_DIR)
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    persona = cfg.personas["Mira"]
    assert cfg.network is not None
    pre_neighbors = {
        name: cfg.network.agents[name].as_dict()
        for name in cfg.network.agents
        if name != "Player"
    }
    machine.tick = 0
    run_trial(
        persona,
        ScenarioConfig(sessions=20, pos_to_neg_ratio=6.0, seed=11),
        veil_machine=machine,
        network=cfg.network,
        focal="Player",
    )
    moved = False
    for name, before in pre_neighbors.items():
        after = cfg.network.agents[name].as_dict()
        if any(abs(after[k] - before[k]) > 1e-9 for k in before):
            moved = True
            break
    assert moved, "L4 propagate did not shift any neighbor stocks"


def test_vulnerability_amplify_injects_when_missing():
    rules = [{"effect": "vulnerability_amplify", "factor": 1.5}]
    ctx = OverrideContext(persona="Test", rules=rules)
    out = pre_apply(ctx, "vulnerability", {})
    assert out.get("affection", 0.0) > 0.0

    ctx2 = OverrideContext(persona="Test", rules=rules)
    out2 = pre_apply(ctx2, "vulnerability", {"trust": 4.0})
    assert out2["trust"] == 4.0 * 1.5


def test_event_row_schema_stable(tmp_path):
    cfg = load_config_dir(CONFIG_DIR)
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    persona = cfg.personas["Mira"]
    events_path = tmp_path / "events.jsonl"
    machine.tick = 0
    run_trial(
        persona,
        ScenarioConfig(sessions=5, pos_to_neg_ratio=5.0, seed=11),
        veil_machine=machine,
        network=cfg.network,
        record_events=True,
        events_path=events_path,
        run_id="test",
    )
    rows = [json.loads(line) for line in events_path.read_text().splitlines() if line]
    assert len(rows) == 5
    expected = {
        "run_id",
        "persona",
        "seed",
        "ratio",
        "session",
        "signal",
        "l1_deltas",
        "post_l5pre_deltas",
        "post_l0_state",
        "veil_state",
        "override_fired",
        "network_neighbors_after",
    }
    for r in rows:
        assert expected <= set(r.keys())
        assert r["run_id"] == "test"
        assert r["persona"] == "Mira"
        assert isinstance(r["post_l0_state"], dict)


def test_analytics_synthetic_trajectory():
    events = [
        {
            "persona": "X",
            "ratio": 5.0,
            "seed": 1,
            "session": i,
            "post_l0_state": {
                "trust": t,
                "affection": 20.0,
                "suspicion": 40.0 - i,
                "resistance": 50.0,
            },
        }
        for i, t in enumerate([30.0, 50.0, 65.0, 55.0, 70.0])
    ]
    m = analytics.metrics_for_trajectory(events)
    assert m["time_to_trust_60"] == 2
    assert m["peak_suspicion"] == 40.0
    assert m["oscillation"] == 2  # +,+,-,+ → 2 sign flips


def test_t_critical_values():
    assert abs(analytics.t_critical(4) - 2.776) < 0.01
    assert abs(analytics.t_critical(100) - 1.96) < 0.05


def test_sweep_with_events_smoke(tmp_path):
    out = sweep(
        CONFIG_DIR,
        sessions=5,
        ratios=(5.0,),
        seeds=(11, 13),
        record_events=True,
        run_id="smoke",
        events_dir=tmp_path,
    )
    assert "analytics" in out
    assert out["analytics"]["cells"]
    assert (tmp_path / "smoke.jsonl").exists()
    cell = out["analytics"]["cells"][0]
    assert "trust" in cell and "ci95" in cell["trust"]


def test_decay_step_without_trait_prior_unchanged():
    """Backward-compat: without trait_prior, decay still pulls toward baselines."""
    state = CoreState(trust=80.0, affection=80.0, suspicion=10.0, resistance=10.0)
    params = CoreParams()
    for _ in range(200):
        decay_step(state, params)
    # trust_baseline=30, suspicion_baseline=20: stocks should drift toward those.
    assert state.trust < 80.0
    assert state.suspicion > 10.0


def test_decay_step_with_trait_prior_targets_prior():
    """trait_prior redirects decay target away from default baselines."""
    state = CoreState(trust=20.0, affection=20.0, suspicion=80.0, resistance=80.0)
    params = CoreParams()
    prior = {"trust": 70.0, "suspicion": 30.0}
    for _ in range(500):
        decay_step(state, params, trait_prior=prior)
    # trust pulled UP toward 70 (vs default baseline 30); suspicion pulled DOWN toward 30.
    assert state.trust > 50.0
    assert state.suspicion < 60.0


def test_prior_shrinkage_rate_scales_decay():
    """prior_shrinkage_rate=0 should freeze stocks listed in trait_prior."""
    s_frozen = CoreState(trust=20.0, affection=20.0, suspicion=80.0, resistance=80.0)
    s_normal = CoreState(trust=20.0, affection=20.0, suspicion=80.0, resistance=80.0)
    p_frozen = CoreParams(prior_shrinkage_rate=0.0)
    p_normal = CoreParams(prior_shrinkage_rate=1.0)
    prior = {"trust": 70.0}
    for _ in range(50):
        decay_step(s_frozen, p_frozen, trait_prior=prior)
        decay_step(s_normal, p_normal, trait_prior=prior)
    assert abs(s_frozen.trust - 20.0) < 1e-6
    assert s_normal.trust > 20.0


def test_state_var_populated_after_run():
    """Per-stock running variance should be non-zero after multi-session run."""
    cfg = load_config_dir(CONFIG_DIR)
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    persona = cfg.personas["Mira"]
    machine.tick = 0
    result = run_trial(
        persona,
        ScenarioConfig(sessions=20, pos_to_neg_ratio=4.0, seed=11),
        veil_machine=machine,
    )
    var_keys = ("trust_var", "affection_var", "suspicion_var", "resistance_var")
    for k in var_keys:
        assert k in result.final_state
        assert result.final_state[k] >= 0.0
    assert any(result.final_state[k] > 0.0 for k in var_keys)


def test_reliability_none_when_short():
    """reliability_split_half is None for trajectories shorter than 4 sessions."""
    events = [
        {
            "post_l0_state": {
                "trust": 30.0,
                "affection": 25.0,
                "suspicion": 50.0,
                "resistance": 70.0,
            },
        }
        for _ in range(3)
    ]
    m = analytics.metrics_for_trajectory(events)
    assert m["reliability_split_half"] is None


def test_reliability_dict_when_long():
    """reliability_split_half returns per-stock floats/None when sessions >= 4."""
    events = [
        {
            "post_l0_state": {
                "trust": 30.0 + i * 2,
                "affection": 25.0 + i,
                "suspicion": 50.0 - i,
                "resistance": 70.0 - i * 1.5,
            },
        }
        for i in range(8)
    ]
    m = analytics.metrics_for_trajectory(events)
    rel = m["reliability_split_half"]
    assert isinstance(rel, dict)
    assert set(rel.keys()) == {"trust", "affection", "suspicion", "resistance"}
    # Monotonic series → strong split-half correlation.
    assert rel["trust"] is not None and rel["trust"] > 0.9


def test_event_jsonl_includes_var_fields(tmp_path):
    """state.{stock}_var fields surface in event JSONL post_l0_state."""
    cfg = load_config_dir(CONFIG_DIR)
    machine = VeilStateMachine(cfg.veil_states, cfg.veil_schedule)
    persona = cfg.personas["Mira"]
    events_path = tmp_path / "events.jsonl"
    machine.tick = 0
    run_trial(
        persona,
        ScenarioConfig(sessions=12, pos_to_neg_ratio=5.0, seed=11),
        veil_machine=machine,
        record_events=True,
        events_path=events_path,
        run_id="vartest",
    )
    rows = [json.loads(line) for line in events_path.read_text().splitlines() if line]
    assert rows
    last = rows[-1]["post_l0_state"]
    for k in ("trust_var", "affection_var", "suspicion_var", "resistance_var"):
        assert k in last


if __name__ == "__main__":
    test_l0_resistance_dissolves_under_trust()
    test_config_loader_boots()
    test_run_trial_per_persona()
    test_sweep_smoke()
    test_l4_propagation_changes_neighbors()
    test_vulnerability_amplify_injects_when_missing()
    test_analytics_synthetic_trajectory()
    test_t_critical_values()
    print("OK")
