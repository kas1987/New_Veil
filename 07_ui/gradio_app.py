"""Veil Town Observatory — Gradio multi-tab dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

import gradio as gr

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

# Ensure observatory package and veil_loader are importable
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from observatory.charts import alignment_trend, veil_timeline  # noqa: E402
from observatory.data import (  # noqa: E402
    read_alignment_series,
    read_beats,
    read_events,
    read_player_state,
    read_queue_jsonl,
    read_replay,
    read_veil_series,
)
from observatory.inspector import (  # noqa: E402
    build_district_tab,
    build_memory_inspector_tab,
    build_quarantine_review_tab,
)
from observatory.live_character import build_live_character_tab  # noqa: E402
from observatory.relationships import build_relationships_tab  # noqa: E402

_MC_DIR = _HERE / "metachromatic_design_system"
_AGENT_CHOICES = [
    "mira",
    "solenne",
    "vael",
    "archivist",
    "witness",
    "threadwatcher",
    "rendered",
]


def _observatory_css() -> str | None:
    """MetaChromatic ops theme for Gradio (harness surface, not in-world VEIL)."""
    token_css = _MC_DIR / "colors_and_type.css"
    theme_css = _MC_DIR / "veil_observatory_theme.css"
    hero_css = _MC_DIR / "hero_page.css"
    if not token_css.is_file():
        return None
    parts = [token_css.read_text(encoding="utf-8")]
    if theme_css.is_file():
        parts.append(theme_css.read_text(encoding="utf-8"))
    if hero_css.is_file():
        parts.append(hero_css.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _render_hero_page(bg_opacity: float) -> str:
    from hero.character_catalog import load_catalog
    from hero.render import render_hero_html

    return render_hero_html(load_catalog(), bg_opacity=bg_opacity)


def _read_scene_queue() -> list[list]:
    rows = read_queue_jsonl(_ROOT / "06_logs" / "scene_prompts.jsonl")
    if not rows:
        return [["(no scene prompts queued)", "", "", "", ""]]
    return [
        [
            r.get("created_at", "")[:19],
            r.get("agent_id", ""),
            r.get("district", ""),
            r.get("veil_state", ""),
            (r.get("positive", "") or "")[:160],
        ]
        for r in rows
    ]


def _read_voice_queue() -> list[list]:
    rows = read_queue_jsonl(_ROOT / "06_logs" / "tts_queue.jsonl")
    if not rows:
        return [["(no voice requests queued)", "", "", "", ""]]
    return [
        [
            r.get("created_at", "")[:19],
            r.get("agent_id", ""),
            r.get("voice_id", ""),
            r.get("emotion", ""),
            (r.get("text", "") or "")[:160],
        ]
        for r in rows
    ]


def _load_orchestrator():
    from veil_loader import load_module

    return load_module("orchestrator", _ROOT / "04_runtime" / "orchestrator.py")


def _trigger_run_once():
    try:
        return _load_orchestrator().run_once()
    except Exception as e:
        return {"error": str(e)}


def _format_status(result: dict) -> str:
    intent = (result.get("intent") or {}).get("label", "—")
    depth = result.get("accumulated_depth", 0.0)
    veil = result.get("veil_state", "calm")
    ps = result.get("player_state") or {}
    dreams = ps.get("dreams_seen", "?")
    turns = ps.get("turns_taken", "?")
    transition = result.get("veil_transition")
    unlocks = result.get("new_unlocks") or []
    beats = result.get("beats_fired") or []
    parts = [
        f"**intent:** `{intent}`",
        f"**depth:** `{depth:.2f}`",
        f"**veil:** `{veil}`",
        f"**dreams:** `{dreams}`",
        f"**turn:** `{turns}`",
    ]
    if transition:
        parts.append(f"**veil-transition:** `{transition}`")
    if unlocks:
        parts.append(f"**unlocked:** `{', '.join(unlocks)}`")
    if beats:
        parts.append(f"**beats:** `{', '.join(beats[:3])}`")
    return " · ".join(parts)


def _run_simulation(n_turns: int):
    orchestrator = _load_orchestrator()
    pairs = [
        ("mira", "player"),
        ("solenne", "player"),
        ("vael", "player"),
        ("archivist", "mira"),
        ("witness", "archivist"),
        ("threadwatcher", "mira"),
        ("rendered", "vael"),
    ]
    n = max(1, min(20, int(n_turns or 3)))
    log = []
    for i in range(n):
        a, b = pairs[i % len(pairs)]
        try:
            result = orchestrator.run_once(agent_id=a, target_agent=b)
            log.append(
                f"Turn {i + 1}: {a} → {b} — action={result.get('action')} "
                f"depth={result.get('accumulated_depth', 0):.2f} "
                f"unlocks={result.get('new_unlocks', [])}"
            )
        except Exception as e:
            log.append(f"Turn {i + 1}: ERROR {e}")
    return "\n".join(log)


def _chat_send(player_text: str, agent_choice: str, history: list):
    orchestrator = _load_orchestrator()
    history = history or []
    if not player_text or not player_text.strip():
        return history, "", ""
    try:
        result = orchestrator.run_once(
            agent_id=agent_choice or "mira",
            target_agent="player",
            player_input=player_text.strip(),
        )
        reply = (
            f"[quarantined — {result.get('reason', 'unknown reason')}]"
            if result.get("action") == "quarantined"
            else result.get("output", "(no output)")
        )
        status = _format_status(result)
    except Exception as e:
        reply = f"[error: {e}]"
        status = f"**error:** `{e}`"
    history.append((player_text.strip(), f"**{agent_choice}:** {reply}"))
    return history, "", status


def app() -> gr.Blocks:
    with gr.Blocks(title="Veil Town Observatory", css=_observatory_css()) as demo:
        gr.Markdown("# Veil Town Observatory")
        gr.Markdown(
            "Observe agent runtime, relationships, quarantined outputs, and "
            "symbolic events. Each tab refreshes on its button click."
        )

        with gr.Tabs():
            with gr.Tab("MetaChromatic Hero"):
                gr.Markdown(
                    "Layered hero portal — taxonomy-driven character cards (PDR-0002). "
                    "Adjust atmosphere opacity to push the background back."
                )
                hero_opacity = gr.Slider(
                    0.05,
                    0.85,
                    value=0.35,
                    step=0.05,
                    label="Background atmosphere opacity",
                )
                hero_html = gr.HTML(label="Hero preview")
                gr.Button("Refresh hero").click(
                    fn=_render_hero_page,
                    inputs=hero_opacity,
                    outputs=hero_html,
                )
                hero_opacity.change(
                    fn=_render_hero_page,
                    inputs=hero_opacity,
                    outputs=hero_html,
                )

            with gr.Tab("Replay Logs"):
                logs_box = gr.Textbox(label="Replay Logs (last 20)", lines=20)
                gr.Button("Refresh logs").click(fn=read_replay, outputs=logs_box)

            build_relationships_tab()

            build_quarantine_review_tab()

            with gr.Tab("Events"):
                ev_df = gr.Dataframe(
                    headers=["timestamp", "type", "agent", "payload (truncated)"],
                    label="Symbolic Events / Dreams / Messages",
                )
                gr.Button("Refresh events").click(fn=read_events, outputs=ev_df)

            with gr.Tab("Veil Timeline"):
                gr.Markdown("Veil state progression over simulation turns.")
                veil_plot = gr.Plot(label="Veil State Timeline")
                gr.Button("Refresh").click(
                    fn=lambda: veil_timeline(read_veil_series()),
                    outputs=veil_plot,
                )

            with gr.Tab("Alignment Trends"):
                gr.Markdown(
                    "Dream alignment scores over time. Green markers = gate passed."
                )
                align_plot = gr.Plot(label="Alignment Trend")
                gr.Button("Refresh").click(
                    fn=lambda: alignment_trend(read_alignment_series()),
                    outputs=align_plot,
                )

            build_memory_inspector_tab()

            build_district_tab()

            with gr.Tab("Run Once"):
                gr.Markdown("Triggers `orchestrator.run_once()` for Mira → Player.")
                result_box = gr.JSON(label="Run result")
                gr.Button("Run Mira → Player").click(
                    fn=_trigger_run_once, outputs=result_box
                )

            with gr.Tab("Scene Queue"):
                gr.Markdown(
                    "ComfyUI scene prompts queued from `image_provider`. "
                    "Enable generation via `VEIL_GENERATE_IMAGES=1`."
                )
                sq_df = gr.Dataframe(
                    headers=[
                        "timestamp",
                        "agent",
                        "district",
                        "veil_state",
                        "positive (trunc.)",
                    ],
                    label="Queued scene prompts",
                )
                gr.Button("Refresh scene queue").click(
                    fn=_read_scene_queue, outputs=sq_df
                )

            with gr.Tab("Voice Queue"):
                gr.Markdown(
                    "TTS requests queued from `voice_provider`. "
                    "Enable generation via `VEIL_GENERATE_VOICE=1`."
                )
                vq_df = gr.Dataframe(
                    headers=[
                        "timestamp",
                        "agent",
                        "voice_id",
                        "emotion",
                        "text (trunc.)",
                    ],
                    label="Queued voice requests",
                )
                gr.Button("Refresh voice queue").click(
                    fn=_read_voice_queue, outputs=vq_df
                )

            with gr.Tab("Narrative Beats"):
                gr.Markdown(
                    "Chronological log of significant moments. Each beat is "
                    "recorded once per (type, label) per player."
                )
                beats_df = gr.Dataframe(
                    headers=["timestamp", "beat_type", "beat_label", "payload"],
                    label="Beats",
                )
                gr.Button("Refresh beats").click(fn=read_beats, outputs=beats_df)

            with gr.Tab("Player State"):
                gr.Markdown(
                    "Cumulative session state. Updates after every `run_once()`."
                )
                ps_box = gr.JSON(label="Player state")
                gr.Button("Refresh state").click(fn=read_player_state, outputs=ps_box)

            with gr.Tab("Simulation"):
                gr.Markdown(
                    "Cycle through agent pairs to advance the world. Useful for warming "
                    "relationships, accumulating depth, and triggering scheduled events."
                )
                sim_n = gr.Slider(1, 20, value=5, step=1, label="Number of turns")
                sim_out = gr.Textbox(label="Simulation log", lines=10)
                gr.Button("Run simulation", variant="primary").click(
                    fn=_run_simulation, inputs=sim_n, outputs=sim_out
                )

            build_live_character_tab(_chat_send, _AGENT_CHOICES)

        demo.load(fn=_render_hero_page, inputs=hero_opacity, outputs=hero_html)

    return demo


if __name__ == "__main__":
    app().launch()
