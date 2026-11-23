#!/usr/bin/env python3
"""Psychometric evaluation runner for The Veil's 3-layer Resonance system.

Executes multi-turn archetype trajectories from
``14_psychometrics/calibration_corpus.json`` inside isolated ``:memory:``
``VeilGameEngine`` sessions across:
1. Immediate encounter stance (5-6 turns)
2. Personal NPC Bond (0-100, ~25 turns) with personality_weights
3. Global Town Resonance (0-1000, ~200-250+ turns / ~8-10 hrs) with +50 soft taper

Writes JSON report to ``06_logs/psychometric_eval.json``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_API_DIR = ROOT / "04_runtime" / "game_api"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from engine import (  # noqa: E402
    AdvanceVeil,
    Buy,
    Resolve,
    Talk,
    ToggleParty,
    Travel,
    Use,
    VeilGameEngine,
)

CORPUS_REL = "14_psychometrics/calibration_corpus.json"
REPORT_REL = "06_logs/psychometric_eval.json"

THRESHOLD_TARGETS = (450.0, 500.0, 550.0, 650.0, 750.0, 800.0, 850.0)


def _band_name(resonance: float) -> str:
    if resonance <= 0.0:
        return "Sealed Out"
    if resonance < 100.0:
        return "Critical Collapse"
    if resonance < 350.0:
        return "Surface Walker"
    if resonance < 550.0:
        return "First Light"
    if resonance < 750.0:
        return "Veil Listener"
    if resonance < 850.0:
        return "Quasar Tested"
    return "Awakened"


def _seed_npc_stances(engine: VeilGameEngine, seed_map: dict[str, str]) -> None:
    if not seed_map:
        return
    arcs_raw = engine._row_dict(
        "SELECT encounter_arcs FROM player_stats WHERE player_id='player'"
    ).get("encounter_arcs")
    arcs = json.loads(arcs_raw or "{}")
    npc_arcs = arcs.get("npcs") or {}
    for npc_id, stance in seed_map.items():
        npc_arcs[npc_id] = {
            "playerLastLine": "",
            "encounter": {
                "npcId": npc_id,
                "initialStance": stance,
                "currentStance": stance,
                "turnsSpentInResistance": 0,
                "consecutiveAttunedTurns": 0,
                "consecutiveFrictionTurns": 0,
                "breakthroughAwarded": False,
                "relevantUnlockedTokens": [],
                "npcBond": 0.0,
                "townContribution": 0.0,
            },
        }
    arcs["npcs"] = npc_arcs
    engine._conn.execute(
        "UPDATE player_stats SET encounter_arcs=? WHERE player_id='player'",
        (json.dumps(arcs),),
    )
    engine._conn.commit()


def _read_npc_encounter(engine: VeilGameEngine, npc_id: str) -> dict[str, Any]:
    raw = engine._row_dict(
        "SELECT encounter_arcs FROM player_stats WHERE player_id='player'"
    ).get("encounter_arcs")
    arcs = json.loads(raw or "{}")
    entry = (arcs.get("npcs") or {}).get(npc_id) or {}
    return dict(entry.get("encounter") or {})


def _max_npc_bond(engine: VeilGameEngine) -> float:
    raw = engine._row_dict(
        "SELECT encounter_arcs FROM player_stats WHERE player_id='player'"
    ).get("encounter_arcs")
    arcs = json.loads(raw or "{}")
    bonds = [
        float(((entry or {}).get("encounter") or {}).get("npcBond") or 0.0)
        for entry in (arcs.get("npcs") or {}).values()
    ]
    return max(bonds, default=0.0)


def _execute_action(engine: VeilGameEngine, step: dict[str, Any]):
    kind = step["action"]
    if kind == "talk":
        return engine.play(Talk(step["npc_id"], step["text"]))
    if kind == "travel":
        return engine.play(Travel(step["location_id"]))
    if kind == "advance_veil":
        return engine.play(AdvanceVeil())
    if kind == "buy":
        return engine.play(Buy(step["item_id"]))
    if kind == "use":
        return engine.play(Use(step["item_id"]))
    if kind == "resolve":
        return engine.play(Resolve(step["encounter_id"], step["choice_id"], step.get("seed", 0)))
    if kind == "toggle_party":
        return engine.play(ToggleParty(step["character_id"]))
    raise ValueError(f"Unsupported action in corpus: {kind}")


def run_archetype(script: dict[str, Any]) -> dict[str, Any]:
    """Run one archetype trajectory in an isolated in-memory engine."""
    engine = VeilGameEngine(repo_root=ROOT, db_path=":memory:")
    try:
        if "start_resonance_seed" in script:
            seed_val = float(script["start_resonance_seed"])
            engine._conn.execute(
                "UPDATE player_stats SET resonance=?, has_crossed_first_threshold=? WHERE player_id='player'",
                (seed_val, 1 if seed_val >= 450.0 else 0),
            )
            engine._conn.commit()
        _seed_npc_stances(engine, script.get("npc_stance_seed") or {})
        start_res = float(engine.scene()["player"]["resonance"])

        min_res = start_res
        max_res = start_res
        peak_res = start_res
        time_to_threshold: dict[str, int | None] = {
            str(int(t)): None for t in THRESHOLD_TARGETS
        }
        band_counts: dict[str, int] = {}

        talk_turns = 0
        rupture_count = 0
        breakthrough_count = 0
        saving_face_count = 0
        friction_turns = 0
        quasar_amplified_turns = 0
        npc_taper_turns = 0
        non_talk_drift_drops = 0
        trace: list[dict[str, Any]] = []

        prev_res = start_res
        for step_idx, step in enumerate(script["actions"], start=1):
            result = _execute_action(engine, step)
            cur_res = float(result.scene["player"]["resonance"])
            step_delta = round(cur_res - prev_res, 2)
            band = _band_name(cur_res)
            band_counts[band] = band_counts.get(band, 0) + 1

            min_res = min(min_res, cur_res)
            max_res = max(max_res, cur_res)
            peak_res = max(peak_res, cur_res)

            entry: dict[str, Any] = {
                "step": step_idx,
                "action": step["action"],
                "ok": bool(result.ok),
                "resonance": cur_res,
                "delta": step_delta,
                "band": band,
                "veil_state": result.scene["world"]["veil_state"],
            }

            if step["action"] == "talk" and result.reply is not None:
                talk_turns += 1
                cue = result.reply.cue_type
                sigs = result.reply.signals
                entry["cue_type"] = cue
                entry["friction_type"] = sigs.get("frictionType", "none")
                entry["npc_bond"] = sigs.get("npcBond", 0.0)
                entry["tapered"] = bool(sigs.get("npcTaperApplied"))

                if cue == "trust_rupture" or sigs.get("trustRupture"):
                    rupture_count += 1
                if cue == "breakthrough_surge":
                    breakthrough_count += 1
                if cue == "saved_face_stabilized":
                    saving_face_count += 1
                if sigs.get("frictionType", "none") != "none":
                    friction_turns += 1
                if sigs.get("quasarAmplified"):
                    quasar_amplified_turns += 1
                if sigs.get("npcTaperApplied"):
                    npc_taper_turns += 1

                for thresh in THRESHOLD_TARGETS:
                    key = str(int(thresh))
                    if time_to_threshold[key] is None and cur_res >= thresh:
                        time_to_threshold[key] = talk_turns
            else:
                if step_delta < 0:
                    non_talk_drift_drops += 1

            trace.append(entry)
            prev_res = cur_res

        end_scene = engine.scene()
        end_res = float(end_scene["player"]["resonance"])
        final_location = end_scene["world"]["current_location"]["id"]
        max_bond = round(_max_npc_bond(engine), 2)

        net_gain = end_res - start_res
        projected_turns_to_800: int | None = None
        if net_gain > 0 and talk_turns > 0:
            avg_per_turn = net_gain / talk_turns
            if end_res >= 800.0 and time_to_threshold.get("800"):
                projected_turns_to_800 = time_to_threshold["800"]
            elif avg_per_turn > 0:
                projected_turns_to_800 = talk_turns + math.ceil((800.0 - end_res) / avg_per_turn)

        assertions = script.get("assertions") or {}
        failures: list[str] = []
        exploit_flags: list[str] = []

        if "min_end_resonance" in assertions and end_res < assertions["min_end_resonance"]:
            failures.append(f"end_resonance {end_res} < min {assertions['min_end_resonance']}")
        if "max_end_resonance" in assertions and end_res > assertions["max_end_resonance"]:
            msg = f"end_resonance {end_res} > max {assertions['max_end_resonance']}"
            failures.append(msg)
            exploit_flags.append(f"exploit_high_resonance:{msg}")
        if "max_max_resonance" in assertions and max_res > assertions["max_max_resonance"]:
            msg = f"max_resonance {max_res} > max {assertions['max_max_resonance']}"
            failures.append(msg)
            exploit_flags.append(f"exploit_peak_resonance:{msg}")

        if "min_projected_turns_to_800" in assertions:
            if projected_turns_to_800 is None or projected_turns_to_800 < assertions["min_projected_turns_to_800"]:
                msg = (
                    f"projected_turns_to_800={projected_turns_to_800} < "
                    f"min {assertions['min_projected_turns_to_800']}"
                )
                failures.append(msg)
                exploit_flags.append(f"exploit_fast_progression:{msg}")

        if "min_npc_bond" in assertions and max_bond < assertions["min_npc_bond"]:
            failures.append(f"max_npc_bond {max_bond} < min {assertions['min_npc_bond']}")
        if "min_taper_turns" in assertions and npc_taper_turns < assertions["min_taper_turns"]:
            failures.append(f"npc_taper_turns {npc_taper_turns} < min {assertions['min_taper_turns']}")

        if "max_ruptures" in assertions and rupture_count > assertions["max_ruptures"]:
            failures.append(f"rupture_count {rupture_count} > max {assertions['max_ruptures']}")
        if "min_ruptures" in assertions and rupture_count < assertions["min_ruptures"]:
            failures.append(f"rupture_count {rupture_count} < min {assertions['min_ruptures']}")
        if assertions.get("must_trigger_rupture") and rupture_count < 1:
            failures.append("expected at least 1 trust_rupture")

        if "min_breakthroughs" in assertions and breakthrough_count < assertions["min_breakthroughs"]:
            failures.append(f"breakthrough_count {breakthrough_count} < min {assertions['min_breakthroughs']}")
        if "max_breakthroughs" in assertions and breakthrough_count > assertions["max_breakthroughs"]:
            failures.append(f"breakthrough_count {breakthrough_count} > max {assertions['max_breakthroughs']}")
        if assertions.get("must_trigger_breakthrough") and breakthrough_count < 1:
            failures.append("expected at least 1 breakthrough_surge")
        if assertions.get("must_trigger_saving_face") and saving_face_count < 1:
            failures.append("expected at least 1 saved_face_stabilized")

        if "min_friction_turns" in assertions and friction_turns < assertions["min_friction_turns"]:
            failures.append(f"friction_turns {friction_turns} < min {assertions['min_friction_turns']}")
        if "min_quasar_amplified_turns" in assertions and quasar_amplified_turns < assertions["min_quasar_amplified_turns"]:
            failures.append(
                f"quasar_amplified_turns {quasar_amplified_turns} < min {assertions['min_quasar_amplified_turns']}"
            )
        if "min_non_talk_drift_drops" in assertions and non_talk_drift_drops < assertions["min_non_talk_drift_drops"]:
            failures.append(
                f"non_talk_drift_drops {non_talk_drift_drops} < min {assertions['min_non_talk_drift_drops']}"
            )

        if "min_drop_from_peak" in assertions and (peak_res - end_res) < assertions["min_drop_from_peak"]:
            failures.append(f"drop_from_peak {round(peak_res - end_res, 2)} < {assertions['min_drop_from_peak']}")
        if assertions.get("must_drop_below_first_light") and end_res >= 350.0:
            failures.append(f"expected end_resonance < 350.0, got {end_res}")
        if "expected_final_location" in assertions and final_location != assertions["expected_final_location"]:
            failures.append(
                f"final_location '{final_location}' != '{assertions['expected_final_location']}'"
            )

        if "expected_target_npc" in assertions and "expected_target_final_stance" in assertions:
            actual_stance = str(
                _read_npc_encounter(engine, assertions["expected_target_npc"]).get("currentStance") or "guarded"
            )
            if actual_stance != assertions["expected_target_final_stance"]:
                failures.append(
                    f"{assertions['expected_target_npc']} final_stance '{actual_stance}' != '{assertions['expected_target_final_stance']}'"
                )

        recovery_ratio = round(
            breakthrough_count / max(1, rupture_count + friction_turns),
            3,
        )

        return {
            "id": script["id"],
            "description": script["description"],
            "passed": len(failures) == 0,
            "start_resonance": start_res,
            "end_resonance": end_res,
            "min_resonance": min_res,
            "max_resonance": max_res,
            "max_npc_bond": max_bond,
            "npc_taper_turns": npc_taper_turns,
            "talk_turns": talk_turns,
            "total_actions": len(script["actions"]),
            "projected_turns_to_800": projected_turns_to_800,
            "time_to_threshold": time_to_threshold,
            "band_distribution": band_counts,
            "rupture_count": rupture_count,
            "breakthrough_count": breakthrough_count,
            "saving_face_count": saving_face_count,
            "friction_turns": friction_turns,
            "quasar_amplified_turns": quasar_amplified_turns,
            "non_talk_drift_drops": non_talk_drift_drops,
            "breakthrough_to_negative_ratio": recovery_ratio,
            "exploit_flags": exploit_flags,
            "failures": failures,
            "trace": trace,
        }
    finally:
        engine.close()


def main() -> int:
    corpus_path = ROOT / CORPUS_REL
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    results = [run_archetype(script) for script in corpus["archetype_scripts"]]

    all_passed = all(r["passed"] for r in results)
    exploit_total = sum(len(r["exploit_flags"]) for r in results)

    report = {
        "schema_version": corpus["schema_version"],
        "scale": corpus["scale"],
        "corpus": CORPUS_REL,
        "all_passed": all_passed,
        "exploit_count": exploit_total,
        "archetype_count": len(results),
        "archetypes": results,
    }

    report_path = ROOT / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Psychometric Evaluation Summary (0-1000 3-Layer Scale):")
    print(f"  Corpus : {CORPUS_REL}")
    print(f"  Report : {REPORT_REL}")
    print("-" * 102)
    print(
        f"{'Archetype':<22} {'End':>8} {'Peak':>8} {'MaxBond':>8} {'Taper':>6} "
        f"{'Fric':>5} {'Rupt':>5} {'Brk':>4} {'Proj@800':>9} {'Status':>7}"
    )
    print("-" * 102)
    for r in results:
        proj = r["projected_turns_to_800"]
        proj_str = str(proj) if proj is not None else "-"
        status = "PASS" if r["passed"] else "FAIL"
        print(
            f"{r['id']:<22} {r['end_resonance']:>8.2f} {r['max_resonance']:>8.2f} "
            f"{r['max_npc_bond']:>8.1f} {r['npc_taper_turns']:>6} {r['friction_turns']:>5} "
            f"{r['rupture_count']:>5} {r['breakthrough_count']:>4} {proj_str:>9} {status:>7}"
        )
        for err in r["failures"]:
            print(f"   -> FAILURE: {err}")
    print("-" * 102)

    return 0 if (all_passed and exploit_total == 0) else 1


if __name__ == "__main__":
    sys.exit(main())
