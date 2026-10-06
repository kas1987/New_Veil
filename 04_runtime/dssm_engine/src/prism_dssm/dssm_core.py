"""DSSM L0 — Core (PURE).

Trust / Affection / Suspicion / Resistance as bounded stocks in [0, 100].
Asymmetric decay (Gottman-flavored): negative stocks sticky, positive volatile.

This module MUST NOT import persona, attachment, veil, or narrative logic.
All character voice and Veil distortion happens upstream of `apply_deltas`.

Key invariant — Resistance dissolves under Trust:
    effective_signal_gain = (1 - resistance_gate * R/100)
    R_decay_bonus = trust_dissolve_k * max(0, T - trust_release_threshold)

Source: Path A canonical core. See REPORT(A) §2-3 for empirical verification.
"""

from __future__ import annotations

from .models import CoreParams, CoreState, clamp


def signal_gain(state: CoreState, params: CoreParams) -> float:
    """Resistance-gated transfer coefficient (always >= 0)."""
    return max(0.0, 1.0 - params.resistance_gate * (state.resistance / 100.0))


def apply_deltas(
    state: CoreState,
    deltas: dict[str, float],
    params: CoreParams,
) -> CoreState:
    """Apply per-stock deltas (output of L1 persona filter / L5 override pipeline).

    Trust/Affection gains are Resistance-gated; Suspicion/Resistance changes apply
    directly. Used by Path-B-style dict pipelines.
    """
    gain = signal_gain(state, params)
    t = float(deltas.get("trust", 0.0))
    a = float(deltas.get("affection", 0.0))
    s = float(deltas.get("suspicion", 0.0))
    r = float(deltas.get("resistance", 0.0))

    state.trust = clamp(state.trust + (gain if t >= 0 else 1.0) * t)
    state.affection = clamp(state.affection + (gain if a >= 0 else 1.0) * a)
    state.suspicion = clamp(state.suspicion + s)
    state.resistance = clamp(state.resistance + r)
    return state


def decay_step(
    state: CoreState,
    params: CoreParams,
    decay_multiplier: float = 1.0,
    trait_prior: dict[str, float] | None = None,
) -> CoreState:
    """Per-session passive decay toward baselines + Resistance dissolution.

    `decay_multiplier` is L3's hook to speed/slow the entire decay schedule
    (entropy engine). 1.0 = nominal physics.

    When `trait_prior` is provided, each named stock decays toward its prior
    instead of the global `<stock>_baseline`, with rate scaled by
    `params.prior_shrinkage_rate`. Stocks not in the prior fall back to baseline.
    """
    m = decay_multiplier
    if trait_prior:
        s = params.prior_shrinkage_rate
        t_target = float(trait_prior.get("trust", params.trust_baseline))
        a_target = float(trait_prior.get("affection", params.affection_baseline))
        sus_target = float(trait_prior.get("suspicion", params.suspicion_baseline))
        r_target = float(trait_prior.get("resistance", params.resistance_baseline))
        t_rate = params.trust_decay * (s if "trust" in trait_prior else 1.0)
        a_rate = params.affection_decay * (s if "affection" in trait_prior else 1.0)
        sus_rate = params.suspicion_decay * (s if "suspicion" in trait_prior else 1.0)
        r_rate = params.resistance_decay * (s if "resistance" in trait_prior else 1.0)
    else:
        t_target = params.trust_baseline
        a_target = params.affection_baseline
        sus_target = params.suspicion_baseline
        r_target = params.resistance_baseline
        t_rate = params.trust_decay
        a_rate = params.affection_decay
        sus_rate = params.suspicion_decay
        r_rate = params.resistance_decay

    state.trust = clamp(state.trust + m * t_rate * (t_target - state.trust))
    state.affection = clamp(state.affection + m * a_rate * (a_target - state.affection))
    state.suspicion = clamp(
        state.suspicion + m * sus_rate * (sus_target - state.suspicion),
    )

    base_decay = m * r_rate * (r_target - state.resistance)
    trust_bonus = params.trust_dissolve_k * max(
        0.0,
        state.trust - params.trust_release_threshold,
    )
    state.resistance = clamp(state.resistance + base_decay - trust_bonus)
    return state
