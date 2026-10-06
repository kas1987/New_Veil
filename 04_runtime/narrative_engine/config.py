r"""
Path configuration for narrative_engine.

Override any path with environment variables:
    PRISM_TAXONOMY_DIR, PRISM_MODELS_DB, PRISM_TTS_SCRIPTS,
    PRISM_SESSIONS_DIR, PRISM_PROFILES_DIR, PRISM_AUDIO_OUT_DIR
"""

import os
from pathlib import Path

# Workspace root = 04_runtime (parent of narrative_engine)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = WORKSPACE_ROOT.parent


def _get(env_key: str, default: Path) -> Path:
    val = os.environ.get(env_key)
    return Path(val) if val else default


TAXONOMY_DIR = _get("PRISM_TAXONOMY_DIR", REPO_ROOT / ".agents" / "nsfw" / "taxonomy")
MODELS_DB = _get("PRISM_MODELS_DB", REPO_ROOT / "models.db")
TTS_SCRIPTS = _get("PRISM_TTS_SCRIPTS", REPO_ROOT / "15_voice" / "scripts")
SESSIONS_DIR = _get("PRISM_SESSIONS_DIR", REPO_ROOT / "06_logs" / "storyboard" / "sessions")
PROFILES_DIR = _get("PRISM_PROFILES_DIR", REPO_ROOT / "13_agents")
AUDIO_OUT_DIR = _get("PRISM_AUDIO_OUT_DIR", REPO_ROOT / "06_logs" / "storyboard" / "audio")
