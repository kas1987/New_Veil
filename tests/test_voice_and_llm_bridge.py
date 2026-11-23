"""Regression tests for 13_agents parity, 15_voice TTS adapter, and live-LLM bridge."""

from __future__ import annotations

import base64
import io
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from veil_loader import load_module

ROOT = Path(__file__).resolve().parents[1]
_API_DIR = ROOT / "04_runtime" / "game_api"
if str(_API_DIR) not in sys.path:
    sys.path.insert(0, str(_API_DIR))

from engine import Talk, VeilGameEngine
from server import create_app

LLM_MOD = load_module("llm_provider", ROOT / "04_runtime" / "llm_provider.py")
QUARANTINE_MOD = load_module("quarantine", ROOT / "05_alignment" / "quarantine.py")
VOICE_PROV = load_module("voice_provider", ROOT / "04_runtime" / "voice_provider.py")
TTS_MOD = load_module("veil_tts_adapter", ROOT / "15_voice" / "tts_adapter.py")


def test_all_15_agents_load_prompt_profile_and_relationships() -> None:
    roster = json.loads((ROOT / "13_agents" / "roster_index.json").read_text(encoding="utf-8"))[
        "characters"
    ]
    assert len(roster) == 15

    for char in roster:
        cid = char["id"]
        assert LLM_MOD.find_agent_dir(cid) is not None
        assert LLM_MOD.load_system_prompt(cid).strip(), f"Empty system_prompt.md for {cid}"
        assert LLM_MOD.load_profile(cid), f"Empty profile.json for {cid}"
        assert LLM_MOD.load_relationships(cid), f"Empty relationships.json for {cid}"
        req = VOICE_PROV.build_tts_request(cid, "Listen to the Prism.")
        assert req["voice_id"]
        assert req["delivery"]


def test_tts_adapter_offline_wav_and_live_http(tmp_path: Path, monkeypatch) -> None:
    queue_file = tmp_path / "tts_queue.jsonl"
    adapter = TTS_MOD.VeilTTSAdapter(queue_path=queue_file)

    offline = adapter.synthesize("mira", "The lanterns remember.", veil_state="quasar_active")
    assert offline["ok"] is True
    assert offline["mode"] == "synthetic_wav"
    assert offline["emotion"] == "intimate_grave"
    assert offline["audio_base64"].startswith("data:audio/wav;base64,")
    raw_wav = base64.b64decode(offline["audio_base64"].split(",", 1)[1])
    assert raw_wav[:4] == b"RIFF"
    assert raw_wav[8:12] == b"WAVE"
    assert queue_file.is_file()
    assert len(queue_file.read_text(encoding="utf-8").splitlines()) == 1

    class _FakeResp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self) -> bytes:
            return json.dumps({"audio_url": "http://127.0.0.1:9911/out/mira.wav"}).encode("utf-8")

    monkeypatch.setenv("VEIL_TTS_URL", "http://127.0.0.1:9911")
    monkeypatch.setattr(TTS_MOD.urllib.request, "urlopen", lambda *a, **kw: _FakeResp())

    live = adapter.synthesize("solenne", "Warmth is a doorway.", queue=False)
    assert live["mode"] == "live"
    assert live["audio_url"] == "http://127.0.0.1:9911/out/mira.wav"


def test_live_llm_talk_bridge_with_alignment_gate(monkeypatch) -> None:
    engine = VeilGameEngine(repo_root=ROOT, db_path=":memory:")
    try:
        monkeypatch.setenv("VEIL_USE_LIVE_LLM", "1")
        monkeypatch.setattr(
            LLM_MOD,
            "generate_agent_output",
            lambda agent_id, user_prompt=None: {
                "output": "Live Prism cadence from Mira beneath the lanterns.",
                "model": "qwen3:8b",
                "fallback": False,
            },
        )
        res = engine.play(
            Talk("mira", "Why do these Caetherra lanterns burn so brightly when dusk falls?")
        )
        assert res.ok is True
        assert res.reply is not None
        assert res.reply.text == "Live Prism cadence from Mira beneath the lanterns."

        # If alignment quarantines the candidate, engine must fall back cleanly to offline beats
        monkeypatch.setattr(
            QUARANTINE_MOD,
            "should_quarantine",
            lambda score_dict, veil_state="calm": (True, "blocked_by_test"),
        )
        res_fallback = engine.play(
            Talk("mira", "I wonder what lies past the surface warmth here?")
        )
        assert res_fallback.ok is True
        assert res_fallback.reply is not None
        assert res_fallback.reply.text != "Live Prism cadence from Mira beneath the lanterns."
    finally:
        engine.close()


def test_voice_and_llm_fastapi_endpoints() -> None:
    app = create_app(db_path=":memory:")
    client = TestClient(app)

    profiles = client.get("/api/voice/profiles")
    assert profiles.status_code == 200
    assert "mira" in profiles.json()["voices"]
    assert "kaelen_lanternwright" in profiles.json()["voices"]

    synth = client.post(
        "/api/voice/synthesize",
        json={"npc_id": "mira", "text": "Step closer to the threshold.", "queue": False},
    )
    assert synth.status_code == 200
    body = synth.json()
    assert body["ok"] is True
    assert body["mode"] == "synthetic_wav"
    assert io.BytesIO(base64.b64decode(body["audio_base64"].split(",", 1)[1])).read(4) == b"RIFF"

    bad_synth = client.post("/api/voice/synthesize", json={"npc_id": "nonexistent", "text": "hi"})
    assert bad_synth.status_code == 404

    llm_stat = client.get("/api/llm/status")
    assert llm_stat.status_code == 200
    assert len(llm_stat.json()["agents_with_prompts"]) == 15

    preview = client.post(
        "/api/dialogue/llm-preview",
        json={"npc_id": "mira", "message": "Why do the lanterns dim?", "execute_live": False},
    )
    assert preview.status_code == 200
    p_body = preview.json()
    assert p_body["ok"] is True
    assert p_body["system_prompt_loaded"] is True
    assert "Why do the lanterns dim?" in p_body["user_prompt"]

    bad_preview = client.post(
        "/api/dialogue/llm-preview",
        json={"npc_id": "missing_npc", "message": "hello"},
    )
    assert bad_preview.status_code == 404
