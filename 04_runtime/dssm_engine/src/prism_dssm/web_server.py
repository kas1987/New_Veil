"""Stdlib HTTP shim that exposes SessionRunner to the prism-console frontend.

Run:  python -m prism_dssm.web_server
Default port 8765. CORS open (dev only).

Endpoints:
    GET  /api/personas
    POST /api/session/start            { persona, seed? }   -> { session_id, snapshot }
    POST /api/session/<id>/step        { signal }           -> StepResult
    POST /api/session/<id>/reset                            -> snapshot
    GET  /api/session/<id>                                  -> snapshot
    GET  /api/signals                                       -> { positive, negative }
"""

from __future__ import annotations

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config_loader import load_config_dir
from .live_session import SessionRunner
from .stress_test_runner import SIGNAL_POOL_NEG, SIGNAL_POOL_POS
from .veil_effects import VeilStateMachine

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"

_cfg = load_config_dir(CONFIG_DIR)
_sessions: dict[str, SessionRunner] = {}


def _make_runner(persona_name: str, seed: int) -> SessionRunner:
    persona = _cfg.personas[persona_name]
    machine = VeilStateMachine(_cfg.veil_states, _cfg.veil_schedule)
    return SessionRunner(
        persona=persona,
        network=_cfg.network,
        seed=seed,
        veil_machine=machine,
    )


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # quieter
        return

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length", "0") or 0)
        if not n:
            return {}
        raw = self.rfile.read(n)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/personas":
            return self._send_json(
                200,
                {
                    "personas": [
                        {
                            "name": n,
                            "archetype": p.archetype,
                            "initial_state": p.initial_state,
                        }
                        for n, p in _cfg.personas.items()
                    ],
                },
            )
        if path == "/api/signals":
            return self._send_json(
                200,
                {
                    "positive": SIGNAL_POOL_POS,
                    "negative": SIGNAL_POOL_NEG,
                },
            )
        if path.startswith("/api/session/"):
            parts = path.strip("/").split("/")
            # /api/session/<id>            -> snapshot
            # /api/session/<id>/<sub>      -> sub-resource
            if len(parts) == 3:
                sid = parts[2]
                runner = _sessions.get(sid)
                if not runner:
                    return self._send_json(404, {"error": "session not found"})
                return self._send_json(200, runner.snapshot())
            if len(parts) == 4:
                sid, sub = parts[2], parts[3]
                runner = _sessions.get(sid)
                if not runner:
                    return self._send_json(404, {"error": "session not found"})
                if sub == "history":
                    return self._send_json(200, {"history": runner.history()})
                if sub == "memories":
                    return self._send_json(200, {"memories": runner.memories()})
                if sub == "missions":
                    return self._send_json(200, {"missions": runner.missions()})
                if sub == "trends":
                    return self._send_json(200, runner.trends())
                if sub == "network":
                    return self._send_json(200, runner.network_state())
        return self._send_json(404, {"error": "not found"})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()

        if path == "/api/session/start":
            persona_name = body.get("persona", "Mira")
            if persona_name not in _cfg.personas:
                return self._send_json(
                    400,
                    {"error": f"unknown persona {persona_name}"},
                )
            seed = int(body.get("seed", 42))
            sid = secrets.token_hex(8)
            _sessions[sid] = _make_runner(persona_name, seed)
            return self._send_json(
                200,
                {
                    "session_id": sid,
                    "snapshot": _sessions[sid].snapshot(),
                },
            )

        parts = path.strip("/").split("/")
        # /api/session/<id>/(step|reset)
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "session":
            sid, action = parts[2], parts[3]
            runner = _sessions.get(sid)
            if not runner:
                return self._send_json(404, {"error": "session not found"})
            if action == "step":
                signal = body.get("signal")
                if not signal:
                    return self._send_json(400, {"error": "signal required"})
                result = runner.step(signal)
                return self._send_json(
                    200,
                    {
                        "session": result.session,
                        "signal": result.signal,
                        "l1_deltas": result.l1_deltas,
                        "post_l5pre_deltas": result.post_l5pre_deltas,
                        "post_l0_state": result.post_l0_state,
                        "veil_state": result.veil_state,
                        "override_fired": result.override_fired,
                        "neighbors": result.neighbors,
                        "snapshot": runner.snapshot(),
                    },
                )
            if action == "reset":
                persona_name = runner.persona.persona
                seed = runner.seed
                _sessions[sid] = _make_runner(persona_name, seed)
                return self._send_json(200, {"snapshot": _sessions[sid].snapshot()})

        return self._send_json(404, {"error": "not found"})


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"[prism_dssm.web_server] listening on http://{host}:{port}")
    print(f"  personas: {sorted(_cfg.personas)}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


if __name__ == "__main__":
    serve()
