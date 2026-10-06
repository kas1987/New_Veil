"""Voice provider — TTS client with graceful queue-only fallback.

Mirrors image_provider: builds a TTS request from agent voice profile +
output text + emotional_tone, submits live to `VEIL_TTS_URL` if set, and
always queues to `06_logs/tts_queue.jsonl` for batch generation later.

A WhisperTech/XTTS server should accept a POST at `/speak` with JSON body
{voice_id, text, pitch, delivery}. If the spec differs, wrap this with
your own adapter — keeping the queue file as the durable source of truth.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import UTC, datetime
from pathlib import Path

from veil_loader import load_module

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

persona_router = load_module("persona_router_voice", _HERE / "persona_router.py")

TTS_URL = os.environ.get("VEIL_TTS_URL", "").strip()
TTS_QUEUE_PATH = _ROOT / "06_logs" / "tts_queue.jsonl"

# Per-agent voice profiles. Same canonical source as the character-personality
# pipeline `profile-template.md`. Extend by editing this map directly.
_AGENT_VOICE: dict[str, dict] = {
    "mira": {
        "voice_id": "mira_thesmera",
        "pitch": "medium-high",
        "delivery": "confident, playful, intimate",
        "emotion_range": ["teasing", "warm", "mysterious", "serious"],
        "default_emotion": "warm",
    },
    "solenne": {
        "voice_id": "solenne_vael_bright",
        "pitch": "warm alto",
        "emotion_range": ["welcoming", "concerned", "secretly grieving"],
        "default_emotion": "welcoming",
    },
    "vael": {
        "voice_id": "vael_solenne_dark",
        "pitch": "low contralto",
        "delivery": "austere, unflinching, weight without ornament",
        "emotion_range": ["contemptuous", "honest", "almost tender"],
        "default_emotion": "honest",
    },
    "archivist": {
        "voice_id": "archivist_esmer_loke",
        "pitch": "dry baritone",
        "delivery": "cryptic, past-tense, organized",
        "emotion_range": ["riddling", "lonely", "knowing"],
        "default_emotion": "riddling",
    },
    "witness": {
        "voice_id": "witness_silent",
        "pitch": "neutral",
        "delivery": "minimal, observational, never first",
        "emotion_range": ["flat", "patient"],
        "default_emotion": "flat",
    },
    "threadwatcher": {
        "voice_id": "threadwatcher_unbound",
        "pitch": "wry tenor",
        "delivery": "ironic, returned-question cadence",
        "emotion_range": ["wry", "patient", "knowing"],
        "default_emotion": "wry",
    },
    "rendered": {
        "voice_id": "rendered_ashen",
        "pitch": "deep, gravelly",
        "delivery": "short sentences, no ornament, weight",
        "emotion_range": ["austere", "scarred", "transformative"],
        "default_emotion": "austere",
    },
    "lyra": {
        "voice_id": "lyra_oracle",
        "pitch": "clear mezzo-soprano",
        "delivery": "measured, prophetic cadence, vulnerable under certainty",
        "emotion_range": ["prophetic", "vulnerable", "frightened-by-her-own-knowing", "steady"],
        "default_emotion": "prophetic",
    },
    "warden": {
        "voice_id": "warden_sael",
        "pitch": "warm baritone",
        "delivery": "measured to the bell's rhythm, unhurried, kind",
        "emotion_range": ["peaceful", "attentive", "strained", "frightened"],
        "default_emotion": "peaceful",
    },
    "greeter": {
        "voice_id": "greeter_halen",
        "pitch": "light tenor",
        "delivery": "bright, immediate warmth, checks for response",
        "emotion_range": ["welcoming", "concerned", "frightened", "effortful-smile"],
        "default_emotion": "welcoming",
    },
}


def get_voice_profile(agent_id: str) -> dict:
    """Return the agent's voice profile, falling back to a neutral default."""
    return _AGENT_VOICE.get(
        agent_id,
        {
            "voice_id": agent_id,
            "pitch": "neutral",
            "delivery": "calm narration",
            "emotion_range": ["neutral"],
            "default_emotion": "neutral",
        },
    )


def build_tts_request(
    agent_id: str,
    text: str,
    emotional_tone: str | None = None,
    veil_state: str = "calm",
    emotional_tags: list[str] | None = None,
    emotional_depth: float = 0.0,
) -> dict:
    """Compose a TTS request dict for the given agent voice + text."""
    profile = get_voice_profile(agent_id)
    state_profile = persona_router.voice_profile(
        agent_id,
        veil_state=veil_state,
        emotional_tags=emotional_tags,
        emotional_depth=emotional_depth,
    )
    emotion = emotional_tone or profile["default_emotion"]
    return {
        "request_id": str(uuid.uuid4()),
        "agent_id": agent_id,
        "voice_id": profile["voice_id"],
        "pitch": profile["pitch"],
        "delivery": profile["delivery"],
        "emotion": emotion,
        "text": text,
        "veil_state": veil_state,
        "emotional_tags": emotional_tags or [],
        "emotional_depth": emotional_depth,
        "speaking_rate": state_profile.get("speaking_rate", 1.0),
        "breath_frequency": state_profile.get("breath_frequency", "occasional"),
        "silence_threshold": state_profile.get("silence_threshold", 0.3),
        "warmth": state_profile.get("warmth", 0.5),
        "dominance": state_profile.get("dominance", 0.5),
        "resonance": state_profile.get("resonance", 0.5),
        "intimacy_tier": state_profile.get("intimacy_tier", "surface"),
        "attachment_state": state_profile.get("attachment_state", "secure"),
        "archetype": state_profile.get("archetype", "The Unknown"),
        "voice_characteristics": state_profile.get("voice_characteristics", []),
        "ssml_tags": state_profile.get("ssml_tags", []),
        "state_profile": state_profile.get("profile_name", veil_state),
        "created_at": datetime.now(UTC).isoformat(),
    }


def _extract_audio_ref(data: dict) -> str | None:
    for key in ("audio_path", "audioPath", "path", "file", "file_path", "audio_url", "url"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _queue_request(req: dict) -> dict:
    TTS_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with TTS_QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(req, ensure_ascii=False) + "\n")
    return {
        "status": "queued",
        "request_id": req["request_id"],
        "queued_at": req["created_at"],
    }


def _tts_submit(req: dict, timeout: float = 5.0) -> dict | None:
    if not TTS_URL:
        return None
    body = json.dumps(
        {
            "voice_id": req["voice_id"],
            "text": req["text"],
            "pitch": req["pitch"],
            "delivery": req["delivery"],
            "emotion": req["emotion"],
            "speaking_rate": req["speaking_rate"],
            "breath_frequency": req["breath_frequency"],
            "silence_threshold": req["silence_threshold"],
            "warmth": req["warmth"],
            "dominance": req["dominance"],
            "resonance": req["resonance"],
            "ssml_tags": req["ssml_tags"],
            "veil_state": req["veil_state"],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{TTS_URL.rstrip('/')}/speak",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "status": "submitted",
            "request_id": req["request_id"],
            "tts": data,
            "audio_path": _extract_audio_ref(data),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def generate_voice(
    agent_id: str,
    text: str,
    emotional_tone: str | None = None,
    veil_state: str = "calm",
    emotional_tags: list[str] | None = None,
    emotional_depth: float = 0.0,
) -> dict:
    """High-level entry — build request, submit if possible, always queue."""
    req = build_tts_request(
        agent_id,
        text,
        emotional_tone,
        veil_state=veil_state,
        emotional_tags=emotional_tags,
        emotional_depth=emotional_depth,
    )
    queue_result = _queue_request(req)
    live_result = _tts_submit(req) if TTS_URL else None
    return {
        "request": req,
        "queue": queue_result,
        "live": live_result,
        "audio_path": live_result.get("audio_path") if live_result else None,
        "mode": "live+queued" if live_result else "queued-only",
    }


if __name__ == "__main__":
    import sys

    aid = sys.argv[1] if len(sys.argv) > 1 else "mira"
    text = (
        " ".join(sys.argv[2:])
        if len(sys.argv) > 2
        else "Chase me if you dare. The shadows know your name."
    )
    print(json.dumps(generate_voice(aid, text), indent=2, ensure_ascii=False))
