"""LLM provider for Veil Town agents — Ollama-backed with graceful fallback.

Reads an agent's system_prompt.md from 02_agents/<id>/ or 13_agents/**/<id>/.
Falls back to a placeholder string if Ollama is unreachable, so the orchestrator
still completes a turn for tests and offline development.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from veil_loader import load_module

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent

_ollama_http = load_module("ollama_http", _HERE / "ollama_http.py")
validate_base_url = _ollama_http.validate_base_url
request_headers = _ollama_http.request_headers

OLLAMA_BASE_URL = validate_base_url(os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
DEFAULT_MODEL = os.environ.get("VEIL_LLM_MODEL", "qwen3:8b")
DEFAULT_TIMEOUT = float(os.environ.get("VEIL_LLM_TIMEOUT", "30"))


_FALLBACK_TEMPLATE = (
    "{agent_title} offers warm Prism guidance while hinting at hidden Dark "
    "Quasar truth through memory and resonance."
)


def find_agent_dir(agent_id: str) -> Path | None:
    """Return the directory containing an agent's profile/prompt files."""
    candidates = [
        _ROOT / "02_agents" / agent_id,
        _ROOT / "13_agents" / "sisters" / agent_id,
        _ROOT / "13_agents" / "supporting" / agent_id,
    ]
    for p in candidates:
        if p.is_dir():
            return p
    # Fallback: scan 13_agents/* for a matching subdir
    base = _ROOT / "13_agents"
    if base.exists():
        for sub in base.iterdir():
            if sub.is_dir():
                hit = sub / agent_id
                if hit.is_dir():
                    return hit
    return None


def load_system_prompt(agent_id: str) -> str:
    """Read system_prompt.md for an agent. Returns empty string if missing."""
    d = find_agent_dir(agent_id)
    if d is None:
        return ""
    f = d / "system_prompt.md"
    if not f.exists():
        return ""
    return f.read_text(encoding="utf-8")


def load_profile(agent_id: str) -> dict:
    """Read profile.json for an agent. Returns empty dict if missing."""
    d = find_agent_dir(agent_id)
    if d is None:
        return {}
    f = d / "profile.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def check_health(base_url: str | None = None, timeout: float = 5.0) -> dict:
    """Probe Ollama `/api/tags`. Returns ok, models, and error when unreachable."""
    resolved = validate_base_url(base_url or OLLAMA_BASE_URL)
    url = f"{resolved}/api/tags"
    try:
        req = urllib.request.Request(url, headers=request_headers())
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        return {"ok": True, "base_url": resolved, "models": models, "error": ""}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError) as e:
        return {"ok": False, "base_url": resolved, "models": [], "error": str(e)}


def _ollama_generate(prompt: str, system: str, model: str, timeout: float) -> str:
    """POST to /api/generate. Raises urllib.error.URLError on connection failure."""
    body = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"num_predict": 220, "temperature": 0.8},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=body,
        headers=request_headers(),
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data.get("response") or "").strip()


def generate_agent_output(
    agent_id: str,
    user_prompt: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
) -> dict:
    """Generate agent output via Ollama. Returns {"output", "model", "fallback"}.

    Falls back to a deterministic placeholder if Ollama is unreachable so the
    orchestrator never hard-fails on infrastructure absence.
    """
    system = load_system_prompt(agent_id)
    if not user_prompt:
        user_prompt = (
            "Speak now to the player. One short, atmospheric utterance "
            "(2-4 sentences). Stay in voice."
        )
    chosen_model = model or DEFAULT_MODEL
    chosen_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT

    try:
        text = _ollama_generate(user_prompt, system, chosen_model, chosen_timeout)
        if not text:
            raise RuntimeError("empty response from Ollama")
        return {"output": text, "model": chosen_model, "fallback": False}
    except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError) as e:
        fallback = _FALLBACK_TEMPLATE.format(agent_title=agent_id.title())
        return {
            "output": fallback,
            "model": "fallback",
            "fallback": True,
            "error": str(e),
        }


if __name__ == "__main__":
    import sys

    aid = sys.argv[1] if len(sys.argv) > 1 else "mira"
    result = generate_agent_output(aid)
    print(json.dumps(result, indent=2, ensure_ascii=False))
