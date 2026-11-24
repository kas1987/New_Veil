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
OPENAI_BASE_URL = validate_base_url(os.environ.get("VEIL_OPENAI_BASE_URL", "http://127.0.0.1:1234"))
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
        _ROOT / "13_agents" / agent_id,
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


def load_relationships(agent_id: str) -> dict:
    """Read relationships.json for an agent. Returns empty dict if missing."""
    d = find_agent_dir(agent_id)
    if d is None:
        return {}
    f = d / "relationships.json"
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


def check_openai_health(base_url: str | None = None, timeout: float = 3.0) -> dict:
    """Probe an OpenAI-compatible `/v1/models` endpoint (LM Studio)."""
    resolved = validate_base_url(
        base_url or os.environ.get("VEIL_OPENAI_BASE_URL") or OPENAI_BASE_URL
    )
    url = f"{resolved}/v1/models"
    try:
        req = urllib.request.Request(url, headers=request_headers())
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("id", "") for m in data.get("data", []) if m.get("id")]
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


def _pick_openai_model(resolved: str, explicit_model: str | None, timeout: float) -> str:
    env_model = os.environ.get("VEIL_LLM_MODEL", "").strip()
    if explicit_model:
        return explicit_model
    if env_model:
        return env_model
    health = check_openai_health(base_url=resolved, timeout=min(timeout, 3.0))
    models = health.get("models") or []
    chat_models = [m for m in models if "embed" not in m.lower()]
    return chat_models[0] if chat_models else (models[0] if models else DEFAULT_MODEL)


def _openai_generate(
    prompt: str,
    system: str,
    model: str | None,
    timeout: float,
    base_url: str | None = None,
) -> tuple[str, str]:
    """POST to `/v1/chat/completions` on LM Studio / OpenAI-compatible servers."""
    resolved = validate_base_url(
        base_url or os.environ.get("VEIL_OPENAI_BASE_URL") or OPENAI_BASE_URL
    )
    chosen = _pick_openai_model(resolved, model, timeout)
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    body = json.dumps(
        {
            "model": chosen,
            "messages": messages,
            "max_tokens": 220,
            "temperature": 0.8,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{resolved}/v1/chat/completions",
        data=body,
        headers=request_headers(),
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    choices = data.get("choices") or []
    first = choices[0] if choices else {}
    msg = first.get("message") or {}
    text = (msg.get("content") or first.get("text") or "").strip()
    return text, chosen


def check_router_status(router_url: str | None = None, timeout: float = 1.5) -> dict:
    """Query Chromatic Router `/status` when ``VEIL_ROUTER_URL`` is configured."""
    raw = (router_url if router_url is not None else os.environ.get("VEIL_ROUTER_URL", "")).strip()
    if not raw:
        return {
            "configured": False,
            "ok": False,
            "holder": "unconfigured",
            "comfy_busy": False,
        }
    try:
        resolved = validate_base_url(raw)
        req = urllib.request.Request(f"{resolved}/status", headers=request_headers())
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        holder = str(data.get("holder") or "unknown")
        comfy_list = data.get("comfy") or []
        comfy_busy = holder in ("comfy", "mixed") or any(
            isinstance(item, dict)
            and (
                item.get("state") == "busy"
                or int(item.get("running") or 0) > 0
                or int(item.get("pending") or 0) > 0
            )
            for item in comfy_list
        )
        return {
            "configured": True,
            "ok": True,
            "base_url": resolved,
            "holder": holder,
            "released": bool(data.get("released")),
            "comfy_busy": comfy_busy,
            "status": data,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
        return {
            "configured": True,
            "ok": False,
            "base_url": raw,
            "holder": "unknown",
            "comfy_busy": False,
            "error": str(exc),
        }


def generate_agent_output(
    agent_id: str,
    user_prompt: str | None = None,
    model: str | None = None,
    timeout: float | None = None,
) -> dict:
    """Generate agent output via Ollama or LM Studio (OpenAI-compatible).

    Defers to deterministic fallback when Chromatic Router reports ComfyUI busy,
    or if neither local LLM backend is reachable.
    """
    router = check_router_status()
    if router.get("ok") and (router.get("comfy_busy") or router.get("holder") in ("comfy", "mixed")):
        holder = router.get("holder", "comfy")
        fallback = _FALLBACK_TEMPLATE.format(agent_title=agent_id.title())
        return {
            "output": fallback,
            "model": "fallback",
            "fallback": True,
            "deferred_by_router": True,
            "router_holder": holder,
            "error": f"Deferred live LLM: Chromatic Router reports GPU held by {holder}",
        }

    system = load_system_prompt(agent_id)
    if not user_prompt:
        user_prompt = (
            "Speak now to the player. One short, atmospheric utterance "
            "(2-4 sentences). Stay in voice."
        )
    chosen_model = model or DEFAULT_MODEL
    chosen_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    backend = os.environ.get("VEIL_LLM_BACKEND", "auto").strip().lower()
    last_err: Exception | None = None

    if backend != "openai":
        try:
            text = _ollama_generate(user_prompt, system, chosen_model, chosen_timeout)
            if not text:
                raise RuntimeError("empty response from Ollama")
            return {"output": text, "model": chosen_model, "fallback": False, "backend": "ollama"}
        except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError) as exc:
            last_err = exc
            if backend == "ollama":
                fallback = _FALLBACK_TEMPLATE.format(agent_title=agent_id.title())
                return {"output": fallback, "model": "fallback", "fallback": True, "error": str(exc)}

    try:
        text, used_model = _openai_generate(user_prompt, system, model, chosen_timeout)
        if not text:
            raise RuntimeError("empty response from OpenAI-compatible backend")
        return {"output": text, "model": used_model, "fallback": False, "backend": "openai"}
    except (urllib.error.URLError, TimeoutError, RuntimeError, OSError, ValueError) as exc:
        err = exc if last_err is None else f"{last_err}; openai: {exc}"
        fallback = _FALLBACK_TEMPLATE.format(agent_title=agent_id.title())
        return {
            "output": fallback,
            "model": "fallback",
            "fallback": True,
            "error": str(err),
        }


if __name__ == "__main__":
    import sys

    aid = sys.argv[1] if len(sys.argv) > 1 else "mira"
    result = generate_agent_output(aid)
    print(json.dumps(result, indent=2, ensure_ascii=False))
