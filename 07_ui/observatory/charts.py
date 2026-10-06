"""Observatory chart builders — pure functions, no I/O, no Gradio imports."""

from __future__ import annotations

import plotly.graph_objects as go

_VEIL_ORDER = {"calm": 1, "still": 2, "storm": 3, "quasar_active": 4}
_VEIL_LABELS = {1: "calm", 2: "still", 3: "storm", 4: "quasar_active"}
_AXES = ["Trust", "Affection", "Suspicion", "Resistance"]


def radar_chart_all(rows: list[dict]) -> go.Figure:
    """One scatterpolar trace per dyad.
    rows: list of dicts with keys agent_a, agent_b, trust, affection, suspicion, resistance."""
    fig = go.Figure()
    for r in rows:
        label = f"{r['agent_a']}→{r['agent_b']}"
        values = [
            float(r.get("trust", 0)),
            float(r.get("affection", 0)),
            float(r.get("suspicion", 0)),
            float(r.get("resistance", 0)),
        ]
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=_AXES + [_AXES[0]],
                name=label,
                fill="toself",
                opacity=0.6,
            )
        )
    fig.update_layout(
        polar={"radialaxis": {"range": [0, 100]}},
        title="CoreState per Dyad",
        showlegend=True,
        margin={"t": 40, "b": 20},
    )
    return fig


def veil_timeline(series: list[dict]) -> go.Figure:
    """Step-line chart of veil state over turns.
    series: [{turn_index, veil_state, accumulated_depth}]."""
    if not series:
        return go.Figure()
    turns = [r["turn_index"] for r in series]
    y_vals = [_VEIL_ORDER.get(r["veil_state"], 1) for r in series]
    depths = [r.get("accumulated_depth", 0.0) for r in series]
    state_names = [r["veil_state"] for r in series]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=turns,
            y=y_vals,
            mode="lines+markers",
            line={"shape": "hv", "width": 2},
            marker={"size": 7},
            customdata=depths,
            text=state_names,
            hovertemplate="Turn %{x}<br>State: %{text}<br>Depth: %{customdata:.2f}<extra></extra>",
            name="Veil State",
        )
    )
    fig.update_layout(
        title="Veil State Over Turns",
        xaxis_title="Turn",
        yaxis=dict(
            tickvals=list(_VEIL_LABELS.keys()),
            ticktext=list(_VEIL_LABELS.values()),
            range=[0.5, 4.5],
        ),
        margin={"t": 40, "b": 40},
    )
    return fig


def alignment_trend(series: list[dict]) -> go.Figure:
    """Scatter+line of prism_resonance over time, color-coded by pass_gate.
    series: [{timestamp, agent_id, prism_resonance, dark_quasar_resonance,
    emotional_depth, pass_gate}]."""
    if not series:
        return go.Figure()
    timestamps = [r["timestamp"][:19] for r in series]
    resonance = [r.get("prism_resonance", 0.0) for r in series]
    pass_colors = ["green" if r.get("pass_gate") else "red" for r in series]
    agents = [r.get("agent_id", "") for r in series]
    pass_vals = [r.get("pass_gate") for r in series]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=resonance,
            mode="lines+markers",
            marker={"color": pass_colors, "size": 8},
            line={"color": "rgba(100,100,200,0.5)", "width": 1},
            text=[f"agent={a} pass={p}" for a, p in zip(agents, pass_vals, strict=True)],
            hovertemplate="%{x}<br>prism_resonance=%{y:.2f}<br>%{text}<extra></extra>",
            name="prism_resonance",
        )
    )
    fig.update_layout(
        title="Dream Alignment Trend (green=pass, red=fail)",
        xaxis_title="Timestamp",
        yaxis={"title": "prism_resonance", "range": [0, 1]},
        margin={"t": 40, "b": 40},
    )
    return fig


def district_status_chart(status: dict) -> go.Figure:
    """Horizontal bar chart: green=unlocked, grey=locked.
    status: {unlocked: [...], locked: [...]}."""
    _ORDER = ["caetherra", "ashveil", "the_hollow"]
    unlocked = set(status.get("unlocked", []))
    colors = ["#3d9970" if d in unlocked else "#aaaaaa" for d in _ORDER]

    fig = go.Figure(
        go.Bar(
            y=_ORDER,
            x=[1, 1, 1],
            orientation="h",
            marker_color=colors,
            text=["unlocked" if d in unlocked else "locked" for d in _ORDER],
            textposition="inside",
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title="District Unlock Status",
        xaxis={"visible": False},
        margin={"t": 40, "b": 20, "l": 120},
        height=200,
    )
    return fig
