"""Observatory — Relationships tab with CoreState radar chart."""

from __future__ import annotations

import gradio as gr

from .charts import radar_chart_all
from .data import read_relationships, read_relationships_chart_data


def _refresh():
    table = read_relationships()
    fig = radar_chart_all(read_relationships_chart_data())
    return table, fig


def build_relationships_tab() -> None:
    """Build the Relationships tab inside the current gr.Blocks context."""
    with gr.Tab("Relationships"):
        rel_df = gr.Dataframe(
            headers=["agent_a", "agent_b", "trust", "affection", "suspicion", "interactions"],
            label="Agent Relationships",
        )
        radar_plot = gr.Plot(label="CoreState Radar — all dyads")
        gr.Button("Refresh").click(fn=_refresh, outputs=[rel_df, radar_plot])
