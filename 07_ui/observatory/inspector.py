"""Observatory — Memory Inspector, District Status, and Quarantine Review tabs."""

from __future__ import annotations

import gradio as gr

from .charts import district_status_chart
from .data import approve_and_promote, read_district_status, read_memories, read_player_state


def build_memory_inspector_tab() -> None:
    with gr.Tab("Memory Inspector"):
        gr.Markdown("Browse persisted memories. Filter by agent and scope.")
        with gr.Row():
            agent_dd = gr.Dropdown(
                choices=[
                    "",
                    "mira",
                    "solenne",
                    "vael",
                    "archivist",
                    "witness",
                    "threadwatcher",
                    "rendered",
                    "player",
                ],
                value="",
                label="Agent (blank = all)",
            )
            scope_dd = gr.Dropdown(
                choices=["", "private", "shared", "event"],
                value="",
                label="Scope (blank = all)",
            )
            limit_sl = gr.Slider(10, 200, value=50, step=10, label="Limit")
        mem_df = gr.Dataframe(
            headers=["id", "scope", "agent_id", "content (120)", "created_at"],
            label="Memories",
        )
        gr.Button("Search").click(
            fn=read_memories,
            inputs=[agent_dd, scope_dd, limit_sl],
            outputs=mem_df,
        )


def build_district_tab() -> None:
    with gr.Tab("Districts"):
        gr.Markdown("Live district unlock status from player state.")
        district_plot = gr.Plot(label="District Unlock Status")
        ps_box = gr.JSON(label="Player state")

        def _refresh():
            fig = district_status_chart(read_district_status())
            return fig, read_player_state()

        gr.Button("Refresh").click(fn=_refresh, outputs=[district_plot, ps_box])


def build_quarantine_review_tab() -> None:
    with gr.Tab("Quarantine Review"):
        gr.Markdown(
            "Review quarantined outputs. Enter an entry ID and click **Approve** "
            "to promote it to shared memory."
        )
        from .data import read_quarantine

        q_df = gr.Dataframe(
            headers=["id", "agent_id", "reason", "content (truncated)"],
            label="Quarantined Outputs",
        )
        with gr.Row():
            entry_id_in = gr.Number(label="Entry ID to approve", precision=0)
            approve_status = gr.Textbox(label="Status", interactive=False)
        with gr.Row():
            approve_btn = gr.Button("Approve + Promote", variant="primary")
            refresh_btn = gr.Button("Refresh list")

        approve_btn.click(
            fn=lambda eid: approve_and_promote(int(eid)),
            inputs=entry_id_in,
            outputs=approve_status,
        )
        refresh_btn.click(fn=read_quarantine, outputs=q_df)
