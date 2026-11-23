"""Local-first TTS synthesis adapter backed by ``15_voice/voice_registry.json``.

Supports optional external HTTP speech synthesis when ``VEIL_TTS_URL`` is
configured, and falls back deterministically to an in-memory 16-bit PCM WAV
harmonic cue matching the speaker's canonical timbre and current ``veil_state``.
"""

from __future__ import annotations

import base64
import io
import json
import math
import os
import struct
import urllib.error
import urllib.parse
import urllib.request
import wave
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
_DEFAULT_REGISTRY = _HERE / "voice_registry.json"
_DEFAULT_QUEUE = _ROOT / "06_logs" / "tts_queue.jsonl"

_TIMBRE_HZ: dict[str, float] = {
    "warm_alto": 220.0,
    "bright_mezzo": 261.63,
    "crisp_contralto": 196.0,
    "ethereal_soprano": 329.63,
    "low_whisper": 146.83,
    "velvet_alto": 207.65,
    "deep_contralto": 164.81,
    "clear_mezzo": 246.94,
    "neutral_resonant": 220.0,
    "calm_baritone": 130.81,
    "dry_tenor": 174.61,
    "metallic_layered": 155.56,
    "soft_baritone": 138.59,
    "friendly_tenor": 185.0,
    "weathered_baritone": 123.47,
}

_VEIL_RATIO: dict[str, float] = {
    "calm": 1.0,
    "still": 0.92,
    "storm": 1.15,
    "quasar_active": 0.78,
}


def _validated_tts_url(raw_url: str | None = None) -> str:
    candidate = (raw_url if raw_url is not None else os.environ.get("VEIL_TTS_URL", "")).strip()
    if not candidate:
        return ""
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"Unsupported VEIL_TTS_URL: {candidate!r}")
    return candidate.rstrip("/")


def render_harmonic_wav(
    freq_hz: float,
    veil_state: str = "calm",
    duration_s: float = 0.18,
    sample_rate: int = 16000,
) -> bytes:
    """Render a deterministic 16-bit mono PCM WAV chime in memory."""
    ratio = _VEIL_RATIO.get(veil_state, 1.0)
    f0 = max(60.0, min(1200.0, freq_hz * ratio))
    n_samples = max(1, int(duration_s * sample_rate))
    frames = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        progress = i / n_samples
        envelope = math.sin(math.pi * progress) ** 1.5
        sample = 0.65 * math.sin(2.0 * math.pi * f0 * t) + 0.35 * math.sin(
            2.0 * math.pi * (f0 * 1.5) * t
        )
        pcm = max(-32767, min(32767, int(sample * envelope * 11000)))
        frames.extend(struct.pack("<h", pcm))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(frames))
    return buf.getvalue()


class VeilTTSAdapter:
    """Voice registry reader and local-first synthesis adapter."""

    def __init__(
        self,
        registry_path: Path | None = None,
        queue_path: Path | None = None,
        tts_url: str | None = None,
    ) -> None:
        self.registry_path = registry_path or _DEFAULT_REGISTRY
        self.queue_path = queue_path or _DEFAULT_QUEUE
        self._explicit_url = tts_url
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        self.voices: dict[str, dict[str, Any]] = dict(data.get("voices") or {})

    def get_profile(self, agent_id: str, veil_state: str = "calm") -> dict[str, Any]:
        entry = self.voices.get(agent_id) or {
            "timbre": "neutral_resonant",
            "cadence": "measured",
            "default_mood": "Warmth",
            "quasar_shift": "grave",
            "xtts_speaker": "Ana Florence",
            "qwen_speaker": "serena",
        }
        timbre = str(entry.get("timbre", "neutral_resonant"))
        mood_key = "quasar_shift" if veil_state == "quasar_active" else "default_mood"
        return {
            "agent_id": agent_id,
            "voice_id": f"{agent_id}_{timbre}",
            "timbre": timbre,
            "cadence": str(entry.get("cadence", "measured")),
            "default_mood": str(entry.get("default_mood", "Warmth")),
            "quasar_shift": str(entry.get("quasar_shift", "grave")),
            "mood": str(entry.get(mood_key, entry.get("default_mood", "Warmth"))),
            "base_hz": _TIMBRE_HZ.get(timbre, 220.0),
            "xtts_speaker": str(entry.get("xtts_speaker", "Ana Florence")),
            "qwen_speaker": str(entry.get("qwen_speaker", "serena")),
        }

    def list_profiles(self, veil_state: str = "calm") -> dict[str, dict[str, Any]]:
        return {aid: self.get_profile(aid, veil_state=veil_state) for aid in self.voices}

    def check_health(self, timeout: float = 2.0) -> dict[str, Any]:
        base_url = _validated_tts_url(self._explicit_url)
        if not base_url:
            return {"ok": False, "configured": False, "base_url": "", "error": "VEIL_TTS_URL unset"}
        req = urllib.request.Request(f"{base_url}/health")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "configured": True, "base_url": base_url, "health": data}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
            return {"ok": False, "configured": True, "base_url": base_url, "error": str(exc)}

    def unload(self, timeout: float = 5.0) -> dict[str, Any]:
        base_url = _validated_tts_url(self._explicit_url)
        if not base_url:
            return {"ok": False, "configured": False, "error": "VEIL_TTS_URL unset"}
        req = urllib.request.Request(
            f"{base_url}/unload",
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return {"ok": True, "base_url": base_url, "result": data}
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
            return {"ok": False, "base_url": base_url, "error": str(exc)}

    def _submit_live(self, payload: dict[str, Any], timeout: float = 45.0) -> dict[str, Any] | None:
        base_url = _validated_tts_url(self._explicit_url)
        if not base_url:
            return None
        req = urllib.request.Request(
            f"{base_url}/speak",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict):
                return data
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError):
            return None
        return None

    def _append_queue(self, record: dict[str, Any]) -> None:
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        with self.queue_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def synthesize(
        self,
        agent_id: str,
        text: str,
        veil_state: str = "calm",
        emotion: str | None = None,
        queue: bool = True,
    ) -> dict[str, Any]:
        profile = self.get_profile(agent_id, veil_state=veil_state)
        resolved_emotion = emotion or profile["mood"]
        clipped_text = text[:240]
        live_payload = {
            "agent_id": agent_id,
            "voice_id": profile["voice_id"],
            "speaker": profile["xtts_speaker"],
            "language": "en",
            "filename": f"veil_{agent_id}.wav",
            "timbre": profile["timbre"],
            "cadence": profile["cadence"],
            "emotion": resolved_emotion,
            "veil_state": veil_state,
            "text": clipped_text,
        }

        live_resp = self._submit_live(live_payload)
        audio_url: str | None = None
        audio_base64: str | None = None
        mode = "synthetic_wav"

        if live_resp:
            for key in ("audio_url", "url", "audio_path", "path", "file_path"):
                val = live_resp.get(key)
                if isinstance(val, str) and val.strip():
                    audio_url = val
                    break
            raw_b64 = live_resp.get("audio_base64")
            if isinstance(raw_b64, str) and raw_b64.strip():
                audio_base64 = raw_b64
            elif audio_url and not audio_url.startswith(("http://", "https://")):
                local_path = Path(audio_url)
                if local_path.is_file():
                    audio_base64 = "data:audio/wav;base64," + base64.b64encode(
                        local_path.read_bytes()
                    ).decode("ascii")
            if audio_url or audio_base64:
                mode = "live"

        if mode != "live":
            wav_bytes = render_harmonic_wav(profile["base_hz"], veil_state=veil_state)
            audio_base64 = "data:audio/wav;base64," + base64.b64encode(wav_bytes).decode("ascii")

        if queue:
            self._append_queue(
                {
                    "created_at": datetime.now(UTC).isoformat(),
                    "agent_id": agent_id,
                    "voice_id": profile["voice_id"],
                    "emotion": resolved_emotion,
                    "veil_state": veil_state,
                    "mode": mode,
                    "text": clipped_text,
                }
            )

        return {
            "ok": True,
            "mode": mode,
            "agent_id": agent_id,
            "profile": profile,
            "emotion": resolved_emotion,
            "veil_state": veil_state,
            "text": clipped_text,
            "mime_type": "audio/wav",
            "audio_base64": audio_base64,
            "audio_url": audio_url,
        }


def synthesize_voice(
    agent_id: str,
    text: str,
    veil_state: str = "calm",
    emotion: str | None = None,
    queue: bool = True,
) -> dict[str, Any]:
    """Module-level helper returning synthesized voice payload."""
    return VeilTTSAdapter().synthesize(
        agent_id=agent_id,
        text=text,
        veil_state=veil_state,
        emotion=emotion,
        queue=queue,
    )
