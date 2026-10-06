"""Voice-Prism drop-in replacement for ElevenLabsAudioDirector.

Same public interface: speak(text, character_key, beat_number, output_path) -> str | None
Uses local ChatterboxEngine (no content restrictions) via direct engine.render() call.
Falls back silently on import or render error.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VOICE_PRISM_SRC = _REPO_ROOT / "Voice-Prism" / "src"

# beat 1-8 → intensity 0.2-1.0 (linear)
_BEAT_INTENSITY = {i: round(0.2 + (i - 1) * (0.8 / 7), 3) for i in range(1, 9)}

_BEAT_SCENE = {
    1: "intro",
    2: "tease",
    3: "build",
    4: "build",
    5: "pre_orgasm",
    6: "peak",
    7: "post_orgasm",
    8: "afterglow",
}

_BEAT_EMOTION = {
    1: "curious",
    2: "anticipation",
    3: "aroused",
    4: "aroused",
    5: "desperate",
    6: "ecstatic",
    7: "relieved",
    8: "satisfied",
}


def _ensure_src() -> bool:
    voice_prism_src = str(_VOICE_PRISM_SRC)
    if voice_prism_src not in sys.path:
        sys.path.insert(0, voice_prism_src)
    try:
        import voice_prism  # noqa: F401

        return True
    except ImportError as e:
        logger.warning(f"voice_prism not importable: {e}")
        return False


class VoicePrismAudioDirector:
    """Local TTS director using Voice-Prism engines. No content restrictions."""

    def __init__(self) -> None:
        self._available = _ensure_src()
        self._engine = None
        if self._available:
            try:
                from voice_prism.engines.registry import ENGINES

                engine_cls = ENGINES.get("chatterbox")
                if engine_cls is None:
                    logger.warning("chatterbox not in Voice-Prism ENGINES registry")
                    self._available = False
                else:
                    self._engine = engine_cls()
                    logger.info("VoicePrismAudioDirector: ChatterboxEngine ready")
            except Exception as e:
                logger.warning(f"VoicePrismAudioDirector init failed: {e}")
                self._available = False

    def speak(
        self,
        text: str,
        character_key: str,
        beat_number: int,
        output_path: str,
    ) -> str | None:
        if not self._available or self._engine is None:
            logger.warning("VoicePrismAudioDirector unavailable — skipping TTS")
            return None
        if not text or not text.strip():
            return None

        beat = max(1, min(8, int(beat_number)))
        intensity = _BEAT_INTENSITY.get(beat, 0.5)
        scene_beat = _BEAT_SCENE.get(beat, "build")
        emotion = _BEAT_EMOTION.get(beat, "aroused")

        try:
            from voice_prism.manifest import Segment

            seg = Segment(
                id=f"{character_key}_beat{beat:02d}",
                text=text,
                emotion=emotion,
                intensity=intensity,
                scene_beat=scene_beat,
                vocalization_type="lexical",
                language="en",
            )

            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            result = self._engine.render(seg, speaker_ref=None, out_path=out)
            if result and Path(result).exists():
                logger.info(f"VoicePrism audio saved: {result}")
                return str(result)
        except Exception as e:
            logger.error(f"VoicePrismAudioDirector.speak error: {e}")

        return None
