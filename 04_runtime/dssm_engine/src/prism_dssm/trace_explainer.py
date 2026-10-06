"""Trace explainer — narrate a single trial's session-by-session trajectory.

Given a JSONL events file produced by ``stress_test_runner.run_trial`` with
``record_events=True``, filter to a single (persona, seed, ratio) trial and
produce a human-readable narrative plus turning-point summary.

Stdlib only. Public API:
    explain_trial(events_path, *, persona, seed, ratio) -> dict
    format_narrative(result) -> str
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .analytics import iter_events

# Win condition: Trust > 60 ∧ Suspicion < 40 ∧ Resistance < 35.
_TRUST_WIN = 60.0
_SUSPICION_WIN = 40.0
_RESISTANCE_WIN = 35.0


def _won(state: dict[str, float]) -> bool:
    return (
        state["trust"] > _TRUST_WIN
        and state["suspicion"] < _SUSPICION_WIN
        and state["resistance"] < _RESISTANCE_WIN
    )


def explain_trial(
    events_path: Path | str,
    *,
    persona: str,
    seed: int,
    ratio: float,
) -> dict:
    """Filter events to the (persona, seed, ratio) trial and narrate it.

    Returns a dict with keys ``lines``, ``turning_points``, ``verdict``.
    Raises ``ValueError`` if no events match the filter.
    """
    path = Path(events_path)
    matched: list[dict] = []
    for ev in iter_events(path):
        if (
            ev.get("persona") == persona
            and int(ev.get("seed", -1)) == int(seed)
            and float(ev.get("ratio", float("nan"))) == float(ratio)
        ):
            matched.append(ev)

    if not matched:
        raise ValueError(
            f"no events for {persona}/seed={seed}/ratio={ratio}",
        )

    matched.sort(key=lambda e: e["session"])

    lines: list[str] = []
    prior_trust: float | None = None
    biggest_drop_session: int | None = None
    biggest_drop_value: float = 0.0  # Most negative delta seen.
    peak_sus_session: int = matched[0]["session"]
    peak_sus_value: float = matched[0]["post_l0_state"]["suspicion"]
    trust_breakthrough_session: int | None = None
    win_session: int | None = None

    for ev in matched:
        session = int(ev["session"])
        st = ev["post_l0_state"]
        t = float(st["trust"])
        a = float(st["affection"])
        s = float(st["suspicion"])
        r = float(st["resistance"])
        veil = ev.get("veil_state") or "None"
        signal = ev.get("signal", "")
        override = bool(ev.get("override_fired", False))
        delta = 0.0 if prior_trust is None else (t - prior_trust)
        sign = "+" if delta >= 0 else "-"
        line = (
            f"S{session:02d} [{veil}] signal={signal}  "
            f"override_fired={override}  "
            f"T={t:.1f} A={a:.1f} S={s:.1f} R={r:.1f} "
            f"(T{sign}{abs(delta):.1f})"
        )
        lines.append(line)

        if trust_breakthrough_session is None and t > _TRUST_WIN:
            trust_breakthrough_session = session
        if s > peak_sus_value:
            peak_sus_value = s
            peak_sus_session = session
        if win_session is None and _won(st):
            win_session = session
        if prior_trust is not None and delta < biggest_drop_value:
            biggest_drop_value = delta
            biggest_drop_session = session

        prior_trust = t

    turning_points: list[dict[str, Any]] = []
    if trust_breakthrough_session is not None:
        turning_points.append(
            {"type": "trust_breakthrough", "session": trust_breakthrough_session},
        )
    turning_points.append(
        {
            "type": "peak_suspicion",
            "session": peak_sus_session,
            "value": peak_sus_value,
        },
    )
    if win_session is not None:
        turning_points.append({"type": "win_achieved", "session": win_session})
    if biggest_drop_session is not None:
        turning_points.append(
            {
                "type": "biggest_drop",
                "session": biggest_drop_session,
                "delta": biggest_drop_value,
            },
        )

    final_trust = float(matched[-1]["post_l0_state"]["trust"])
    if win_session is not None:
        verdict = "won"
    elif trust_breakthrough_session is not None and final_trust < _TRUST_WIN:
        verdict = "regressed"
    elif trust_breakthrough_session is None:
        verdict = "stalled"
    else:
        # Trust crossed 60 but full win condition never met; treat as stalled.
        verdict = "stalled"

    return {
        "lines": lines,
        "turning_points": turning_points,
        "verdict": verdict,
        "_meta": {
            "persona": persona,
            "seed": seed,
            "ratio": ratio,
            "sessions": len(matched),
            "win_session": win_session,
        },
    }


def format_narrative(result: dict) -> str:
    """Render explain_trial output as a multiline string."""
    meta = result.get("_meta", {})
    persona = meta.get("persona", "?")
    seed = meta.get("seed", "?")
    ratio = meta.get("ratio", "?")
    sessions = meta.get("sessions", len(result.get("lines", [])))
    verdict = result.get("verdict", "?")
    win_session = meta.get("win_session")

    parts: list[str] = []
    parts.append(
        f"Trial: {persona} | seed={seed} | ratio={ratio} | sessions={sessions}",
    )
    if verdict == "won" and win_session is not None:
        parts.append(f"Verdict: WON at session {win_session}")
    else:
        parts.append(f"Verdict: {verdict.upper()}")
    parts.append("")
    parts.extend(result.get("lines", []))
    parts.append("")
    parts.append("Turning points:")
    for tp in result.get("turning_points", []):
        kind = tp.get("type")
        if kind == "trust_breakthrough":
            parts.append(f"- Trust breakthrough at S{tp['session']:02d}")
        elif kind == "peak_suspicion":
            parts.append(
                f"- Peak suspicion {tp['value']:.1f} at S{tp['session']:02d}",
            )
        elif kind == "win_achieved":
            parts.append(f"- Win achieved at S{tp['session']:02d}")
        elif kind == "biggest_drop":
            parts.append(
                f"- Biggest trust drop {tp['delta']:.1f} at S{tp['session']:02d}",
            )
        else:
            parts.append(f"- {kind} {tp}")
    return "\n".join(parts)
