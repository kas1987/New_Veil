"""Runtime configuration for Veil Town."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RuntimeConfig:
    """Configuration for the Veil Town runtime."""
    db_path: str = os.environ.get("VEIL_DB_PATH", "03_memory/veil_town.sqlite")
    log_path: str = os.environ.get("VEIL_LOG_PATH", "06_logs/replay.jsonl")
    veil_config: str = "04_runtime/veil_engine/configs/veil_states.json"
    model_provider: str = os.environ.get("VEIL_MODEL_PROVIDER", "ollama")
    model_name: str = os.environ.get("VEIL_MODEL_NAME", "llama3.1")
    mode: str = os.environ.get("VEIL_RUNTIME_MODE", "local")
    max_ticks: int = 0
    tick_interval: float = 1.0
    kill_switch_file: str = ".veil_kill_switch"
    alignment_rules: str = "05_alignment/rules.json"
    quarantine_drift_threshold: float = 0.35
    quarantine_canon_threshold: float = 0.75
    memory_limit: int = 1000
    ui_host: str = "0.0.0.0"
    ui_port: int = 7860
    veil_root: str = os.environ.get("VEIL_ROOT", "")
    veil_tts_repo_root: str = os.environ.get("VEIL_TTS_REPO_ROOT", "")


_config: RuntimeConfig | None = None


def get_config() -> RuntimeConfig:
    global _config
    if _config is None:
        _config = RuntimeConfig()
    return _config


def reset_config() -> None:
    global _config
    _config = None


def should_stop(config: RuntimeConfig) -> bool:
    return Path(config.kill_switch_file).exists()
