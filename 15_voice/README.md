# 15_voice

Voice profiles, mood cues, and the local-first TTS synthesis surface for Veil Town.

## Files

- `voice_registry.json`: Canonical voice profiles (`timbre`, `cadence`, `default_mood`, `quasar_shift`) for all 15 characters in `13_agents/roster_index.json`.
- `tts_adapter.py`: `VeilTTSAdapter` and `synthesize_voice()` providing:
  - Optional live HTTP synthesis when `VEIL_TTS_URL` is configured (`POST {VEIL_TTS_URL}/speak` with `{agent_id, voice_id, timbre, cadence, emotion, veil_state, text}`).
  - Deterministic in-memory 16-bit PCM WAV harmonic chime fallback (`audio/wav` base64 data URI) when offline or `VEIL_TTS_URL` is unset.
  - Durable queue logging to `06_logs/tts_queue.jsonl` without embedding machine-local paths in the repo.

## FastAPI Routes (`04_runtime/game_api/server.py`)

- `GET /api/voice/profiles`: Lists voice profiles and resolved moods for the current `veil_state`.
- `POST /api/voice/synthesize`: Synthesizes a character's voice cue (`npc_id`, `text`, optional `veil_state`, `emotion`, `queue`).
