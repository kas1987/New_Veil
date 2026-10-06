"""
Narrative engine REST API — port 5001.

Endpoints:
    GET  /api/narrative/health
    POST /api/narrative/session   { characterKey, beatStart? }
    POST /api/narrative/turn      { sessionId, userText, beat, characterKey }
    GET  /api/narrative/state/<session_id>

Run:
    python narrative_engine/server.py
    python narrative_engine/server.py --port 5001
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid

# Ensure workspace root is on path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask, jsonify, request
from flask_cors import CORS
from narrative_engine.config import AUDIO_OUT_DIR, TAXONOMY_DIR
from narrative_engine.core import InteractiveNarrativeEngine

app = Flask(__name__)
CORS(app)

# In-memory session registry  { session_id: InteractiveNarrativeEngine }
_sessions: dict[str, InteractiveNarrativeEngine] = {}


def _get_or_create(session_id: str, character_key: str, beat_start: int) -> InteractiveNarrativeEngine:
    if session_id not in _sessions:
        engine = InteractiveNarrativeEngine(
            character_key=character_key,
            taxonomy_dir=str(TAXONOMY_DIR),
            audio_out_dir=str(AUDIO_OUT_DIR),
            session_id=session_id,
        )
        engine.beat = beat_start
        engine._beat = beat_start
        _sessions[session_id] = engine
    return _sessions[session_id]


# ── Health ─────────────────────────────────────────────────────────────────────


@app.get("/api/narrative/health")
def health():
    return jsonify({"status": "ok", "sessions": len(_sessions)})


# ── Start session ──────────────────────────────────────────────────────────────


@app.post("/api/narrative/session")
def start_session():
    body = request.get_json(force=True) or {}
    character_key = body.get("characterKey", "russian")
    beat_start = int(body.get("beatStart", 1))
    session_id = str(uuid.uuid4())
    _get_or_create(session_id, character_key, beat_start)
    return jsonify(
        {
            "sessionId": session_id,
            "characterKey": character_key,
            "beat": beat_start,
        }
    )


# ── Process a user turn ────────────────────────────────────────────────────────


@app.post("/api/narrative/turn")
def process_turn():
    body = request.get_json(force=True) or {}
    session_id = body.get("sessionId", "")
    user_text = body.get("userText", "")
    beat = int(body.get("beat", 1))
    character_key = body.get("characterKey", "russian")

    if not session_id:
        return jsonify({"error": "sessionId required"}), 400
    try:
        uuid.UUID(str(session_id))
    except ValueError:
        return jsonify({"error": "sessionId invalid"}), 400
    if not user_text:
        return jsonify({"error": "userText required"}), 400

    engine = _get_or_create(session_id, character_key, beat)

    try:
        response_text, audio_path = engine.process_turn(
            user_input=user_text,
            character_key=character_key,
            beat=beat,
        )
    except Exception:
        import logging

        logging.getLogger("NarrativeEngine").exception("narrative turn failed")
        return jsonify({"error": "turn failed"}), 500

    arc_state = engine.llm._resolve_arc_state(engine.beat - 1, engine.state.arousal, character_key)

    return jsonify(
        {
            "responseText": response_text,
            "audioPath": str(audio_path) if audio_path else None,
            "arcState": arc_state,
            "state": engine.state.to_dict(),
            "beat": engine.beat - 1,
        }
    )


# ── Read session state ─────────────────────────────────────────────────────────


@app.get("/api/narrative/state/<session_id>")
def get_state(session_id: str):
    engine = _sessions.get(session_id)
    if not engine:
        return jsonify({"error": "session not found"}), 404

    arc_state = engine.llm._resolve_arc_state(engine.beat, engine.state.arousal, engine.character_key or "")
    return jsonify(
        {
            "sessionId": session_id,
            "beat": engine.beat,
            "arcState": arc_state,
            "characterKey": engine.character_key,
            "state": engine.state.to_dict(),
            "historyLength": len(engine._history),
        }
    )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    app.run(host=args.host, port=args.port, debug=False)
