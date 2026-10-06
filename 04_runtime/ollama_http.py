"""Shared Ollama HTTP guards for Veil Town — localhost policy and optional auth."""

from __future__ import annotations

import os
from urllib.parse import urlparse

_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})


def allow_remote_ollama() -> bool:
    return os.environ.get("VEIL_OLLAMA_ALLOW_REMOTE", "0").lower() in ("1", "true", "yes")


def validate_base_url(base_url: str) -> str:
    """Return normalized base URL or raise ValueError if not permitted."""
    raw = (base_url or "").strip().rstrip("/")
    if not raw:
        raise ValueError("OLLAMA_BASE_URL is empty")
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"OLLAMA_BASE_URL must be http(s): {raw!r}")
    host = (parsed.hostname or "").lower()
    if not allow_remote_ollama() and host not in _LOCAL_HOSTS:
        raise ValueError(
            f"OLLAMA_BASE_URL host {host!r} is not localhost. "
            "Set VEIL_OLLAMA_ALLOW_REMOTE=1 only if you accept remote inference risk."
        )
    return raw


def request_headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def live_tests_enabled() -> bool:
    return os.environ.get("VEIL_OLLAMA_LIVE", "0").lower() in ("1", "true", "yes")
