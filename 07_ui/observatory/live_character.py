"""Interactive Live Character GUI tab (PDR-0004)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import gradio as gr
from live_character_context import (
    format_presence,
    refresh_live_context,
    suggested_prompts,
)


def build_live_character_tab(
    chat_send: Callable[..., Any],
    agent_choices: list[str],
) -> None:
    """Build the Live Character tab inside the current gr.Blocks context."""
    with gr.Tab("Live Character"):
        gr.Markdown(
            "Interactive persona surface — presence, conversation, telemetry, memory, and soft branch prompts."
        )
        agent_choice = gr.Dropdown(
            choices=agent_choices,
            value=agent_choices[0] if agent_choices else "mira",
            label="Active character",
        )
        presence_md = gr.Markdown(value=format_presence(agent_choices[0] if agent_choices else "mira"))
        telemetry_json = gr.JSON(label="Persona telemetry (player dyad)")

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(label="Conversation stream", height=360)
                msg_in = gr.Textbox(
                    label="You say…",
                    placeholder="Speak softly. Or sharply. Choose.",
                )
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")
                status_bar = gr.Markdown("**status:** _waiting for first input_")
            with gr.Column(scale=2):
                gr.Markdown("#### Memory / context drawer")
                memory_df = gr.Dataframe(
                    headers=["id", "scope", "agent", "content", "created_at"],
                    label="Recent memories",
                )
                branch_md = gr.Markdown(
                    value=suggested_prompts(agent_choices[0] if agent_choices else "mira")
                )

        agent_choice.change(
            fn=refresh_live_context,
            inputs=agent_choice,
            outputs=[presence_md, telemetry_json, memory_df, branch_md],
        )

        def _send_and_refresh(player_text, agent, history):
            history, cleared, status = chat_send(player_text, agent, history)
            presence, telemetry, memories, branch = refresh_live_context(agent)
            return history, cleared, status, presence, telemetry, memories, branch

        send_btn.click(
            fn=_send_and_refresh,
            inputs=[msg_in, agent_choice, chatbot],
            outputs=[chatbot, msg_in, status_bar, presence_md, telemetry_json, memory_df, branch_md],
        )
        msg_in.submit(
            fn=_send_and_refresh,
            inputs=[msg_in, agent_choice, chatbot],
            outputs=[chatbot, msg_in, status_bar, presence_md, telemetry_json, memory_df, branch_md],
        )
        clear_btn.click(
            fn=lambda agent: ([], "", "**status:** _cleared_", *refresh_live_context(agent)),
            inputs=agent_choice,
            outputs=[chatbot, msg_in, status_bar, presence_md, telemetry_json, memory_df, branch_md],
        )
