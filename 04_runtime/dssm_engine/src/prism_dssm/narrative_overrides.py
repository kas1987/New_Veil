"""DSSM L5 — Narrative Override.

Sister archetypes bend the rules. Three hooks:
    pre_apply(ctx, signal, deltas)  — mutate deltas BEFORE L0
    post_apply(ctx, signal)         — record history AFTER L0
    tick_pending(ctx)               — advance delayed effects, return due deltas

Effects supported (driven by JSON `override_rules`):
    delayed_trust_gain     — Mira: failure → curiosity spike → +trust at delay_turns
    block_negative_trust   — Mira: negative deltas don't reduce trust
    mirror_player          — Shadow: Tit-for-Tat with memory amplification
    punish_optimization    — Elias: repeated identical positives → +resistance
    vulnerability_amplify  — generic: boost vulnerability response

Source: Path B canonical L5.
"""

from __future__ import annotations

from typing import Any

from .models import OverrideContext

POSITIVE_SIGNALS = {"compliment", "vulnerability", "support", "gift", "honesty"}
NEGATIVE_SIGNALS = {"silence", "criticism", "deception", "withdrawal", "betrayal"}


def signal_valence(signal: str) -> int:
    if signal in POSITIVE_SIGNALS:
        return 1
    if signal in NEGATIVE_SIGNALS:
        return -1
    return 0


def make_context(persona: str, rules: list[dict[str, Any]]) -> OverrideContext:
    return OverrideContext(persona=persona, rules=rules)


def pre_apply(
    ctx: OverrideContext,
    signal: str,
    deltas: dict[str, float],
) -> dict[str, float]:
    """Mutate `deltas` before they hit L0. Returns the adjusted dict."""
    out = dict(deltas)
    val = signal_valence(signal)

    for rule in ctx.rules:
        effect = rule.get("effect")
        trigger = rule.get("trigger", "always")

        if effect == "block_negative_trust":
            if out.get("trust", 0.0) < 0.0:
                out["trust"] = 0.0

        elif effect == "delayed_trust_gain":
            if trigger == "failure" and val < 0:
                delay = int(rule.get("delay_turns", 3))
                amount = float(rule.get("amount", 6.0))
                ctx.pending.append((delay, {"trust": amount}))

        elif effect == "mirror_player":
            same_val_recent = sum(1 for _, v in ctx.history if v == val)
            amp = 1.0 + 0.15 * same_val_recent
            if val > 0:
                out["trust"] = out.get("trust", 0.0) * amp
            elif val < 0:
                out["suspicion"] = (
                    out.get("suspicion", 0.0) * amp + 1.5 * same_val_recent
                )

        elif effect == "punish_optimization":
            last = ctx.counters.get("last_signal", "")
            if signal == last and val > 0:
                streak = ctx.counters.get("streak", 0) + 1
                ctx.counters["streak"] = streak
                if streak >= int(rule.get("streak_threshold", 3)):
                    out["resistance"] = out.get("resistance", 0.0) + float(
                        rule.get("resistance_penalty", 4.0),
                    )
            else:
                ctx.counters["streak"] = 0
            ctx.counters["last_signal"] = signal

        elif effect == "vulnerability_amplify":
            if signal == "vulnerability":
                factor = float(rule.get("factor", 1.5))
                amplified_any = False
                for k in ("trust", "affection"):
                    if k in out and out[k] > 0:
                        out[k] *= factor
                        amplified_any = True
                if not amplified_any:
                    # L1 emitted neither trust nor affection — make rule visible.
                    out["affection"] = out.get("affection", 0.0) + (factor - 1.0)
    return out


def post_apply(ctx: OverrideContext, signal: str) -> None:
    ctx.history.append((signal, signal_valence(signal)))


def tick_pending(ctx: OverrideContext) -> dict[str, float]:
    due: dict[str, float] = {}
    new_pending: list[tuple[int, dict[str, float]]] = []
    for turns, deltas in ctx.pending:
        if turns <= 1:
            for k, v in deltas.items():
                due[k] = due.get(k, 0.0) + v
        else:
            new_pending.append((turns - 1, deltas))
    ctx.pending = new_pending
    return due
