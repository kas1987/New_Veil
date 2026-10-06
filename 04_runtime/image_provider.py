"""Image provider — ComfyUI client with graceful queue-only fallback.

Builds scene prompts from agent traits + district mood + current veil state.
Two modes:

  1. **Live** — if `VEIL_COMFYUI_URL` is set and the server is reachable, POST
     a workflow JSON to ComfyUI's `/prompt` endpoint and return the prompt id.
  2. **Queued** — append the prompt to `06_logs/scene_prompts.jsonl` so any
     downstream batch generator (or human running ComfyUI later) can consume
     them in order.

The queued mode is always safe — it lets the runtime stay productive even
without a GPU/ComfyUI online.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

COMFYUI_URL = os.environ.get("VEIL_COMFYUI_URL", "").strip()
PROMPT_QUEUE_PATH = _ROOT / "06_logs" / "scene_prompts.jsonl"

# Per-agent visual tag banks. Drawn from the Veil canon + character pipeline
# profile-template. Extend by editing this map rather than scattering tags
# across many profile.json files.
_AGENT_VISUAL_TAGS: dict[str, list[str]] = {
    "mira": [
        "gothic elegance",
        "intelligent eyes",
        "mischievous smile",
        "steampunk mystic fashion",
        "warm lantern light",
    ],
    "solenne": [
        "radiant maternal warmth",
        "long pale robes",
        "soft golden hair",
        "tired but kind eyes",
        "dawn-coloured palette",
    ],
    "vael": [
        "austere figure in dark cloth",
        "unflinching gaze",
        "ash-grey palette",
        "long dark hair",
        "raised dais shadow",
    ],
    "archivist": [
        "ancient librarian",
        "spectacles glinting",
        "ink-stained fingers",
        "leather-bound tomes",
        "dim candlelit interior",
    ],
    "witness": [
        "obscure figure in deep hood",
        "barely-glimpsed silhouette",
        "monochrome palette",
        "still as carved stone",
    ],
    "threadwatcher": [
        "liminal figure between worlds",
        "robes woven of grey thread",
        "wry expression",
        "neither warm nor cold lighting",
    ],
    "rendered": [
        "ash-marked face",
        "iron-and-scar palette",
        "scarred hands",
        "quiet menace",
        "industrial forge backdrop",
    ],
    "lyra": [
        "oracle's distant gaze",
        "silver-threaded robes",
        "calm authority",
        "light both warm and cold",
        "symbols inked on palms",
    ],
    "warden": [
        "serene monastery keeper",
        "white stone backdrop",
        "soft stilling bell light",
        "gentle hands",
        "weathered patience",
    ],
    "greeter": [
        "warm smile at the door",
        "lantern in both hands",
        "welcoming posture",
        "gold-lit cobblestones",
        "genuine kindness in eyes",
    ],
}

_DISTRICT_MOODS: dict[str, str] = {
    "caetherra": "warm cobblestone streets, lantern-lit, soft welcoming light",
    "ashveil": "industrial ruins, ash drifting through air, iron and orange forge glow",
    "ember_vaults": "subterranean archive, ember casket glow, memory anvil, sealed vault doors, warm dark",
    "the_hollow": "liminal dreamscape, void doors flickering, near-monochrome with subtle prism rainbows",
    "stillward": "white stone monastery, soft bell resonance, prayer mirrors, serene peace",
}

_VEIL_STATE_MODIFIERS: dict[str, str] = {
    "calm": "serene composition, balanced light",
    "still": "quiet stillness, faint dust motes, held breath atmosphere",
    "storm": "tense atmosphere, stormy sky behind, agitated air",
    "quasar_active": "gravitational distortion, prismatic chromatic aberration, dark heavy weight pulling at edges",
}


def build_scene_prompt(
    agent_id: str,
    district: str = "caetherra",
    veil_state: str = "calm",
    extra_tags: list[str] | None = None,
) -> dict:
    """Compose a positive/negative prompt pair from agent + district + veil state."""
    agent_tags = _AGENT_VISUAL_TAGS.get(agent_id, [agent_id])
    district_mood = _DISTRICT_MOODS.get(district, "")
    veil_modifier = _VEIL_STATE_MODIFIERS.get(veil_state, "")

    positive_parts = list(agent_tags)
    if district_mood:
        positive_parts.append(district_mood)
    if veil_modifier:
        positive_parts.append(veil_modifier)
    if extra_tags:
        positive_parts.extend(extra_tags)
    positive_parts.append("painterly, cinematic, atmospheric depth of field")

    positive = ", ".join(positive_parts)
    negative = "low quality, blurry, distorted anatomy, watermark, signature, text"

    return {
        "prompt_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "district": district,
        "veil_state": veil_state,
        "positive": positive,
        "negative": negative,
        "created_at": datetime.now(UTC).isoformat(),
    }


def _queue_prompt(prompt: dict) -> dict:
    """Append the prompt to the queue file. Always succeeds."""
    PROMPT_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROMPT_QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(prompt, ensure_ascii=False) + "\n")
    return {
        "status": "queued",
        "prompt_id": prompt["prompt_id"],
        "queued_at": prompt["created_at"],
    }


def _comfyui_submit(prompt: dict, timeout: float = 5.0) -> dict | None:
    """Submit the prompt to ComfyUI. Returns the response dict or None on failure.

    NOTE: A real ComfyUI workflow JSON depends on the user's exact node graph,
    so this function submits a minimal payload that includes the positive/negative
    text as a `text_prompt` field. Users running ComfyUI should wrap this with
    their own workflow template if they want full SDXL/Flux output.
    """
    if not COMFYUI_URL:
        return None
    body = json.dumps(
        {
            "client_id": prompt["prompt_id"],
            "text_prompt": {
                "positive": prompt["positive"],
                "negative": prompt["negative"],
            },
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL.rstrip('/')}/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"status": "submitted", "prompt_id": prompt["prompt_id"], "comfy": data}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def generate_scene_image(
    agent_id: str,
    district: str = "caetherra",
    veil_state: str = "calm",
    extra_tags: list[str] | None = None,
) -> dict:
    """High-level entry point — build prompt, submit if possible, always queue."""
    prompt = build_scene_prompt(agent_id, district, veil_state, extra_tags)
    # Always queue so we have an audit trail even when live submission succeeds.
    queue_result = _queue_prompt(prompt)
    live_result = _comfyui_submit(prompt) if COMFYUI_URL else None
    return {
        "prompt": prompt,
        "queue": queue_result,
        "live": live_result,
        "mode": "live+queued" if live_result else "queued-only",
    }


if __name__ == "__main__":
    import sys

    aid = sys.argv[1] if len(sys.argv) > 1 else "mira"
    dst = sys.argv[2] if len(sys.argv) > 2 else "caetherra"
    vs = sys.argv[3] if len(sys.argv) > 3 else "calm"
    result = generate_scene_image(aid, dst, vs)
    print(json.dumps(result, indent=2, ensure_ascii=False))
