# Voice-Prism

Best-of-breed multi-engine TTS / voice modeling platform. Mirrors the
Image-Prism architecture: routes each performance axis (timbre, prosody,
emotion, non-lexical vocalization, language) to whichever engine wins a
per-axis benchmark.

## Architecture

```
        +---------------------+
script  |  PerformanceManifest|  (Pydantic IR)
 ---->  |  segments[]         |
        +----------+----------+
                   |
                   v
        +----------+----------+        +-----------------+
        |  Axis Router        | -----> | Engine Registry |
        +----------+----------+        +--------+--------+
                   |                            |
                   v                            v
        +----------+----------+        +-----------------+
        |  Render Pipeline    | <----> | CosyVoice3 etc. |
        +----------+----------+        +-----------------+
                   |
                   v
              WAV / FLAC
```

## Engine Slate

| Engine        | Strength                     |
|---------------|------------------------------|
| CosyVoice3    | Instruct prosody / emotion   |
| Chatterbox    | Expressive zero-shot         |
| F5-TTS        | Fast flow-matching baseline  |
| XTTS-v2       | Multilingual cloning         |
| RVC           | Timbre conversion            |
| Qwen3-TTS     | Long-form coherence          |
| IndexTTS      | Index-based zero-shot        |
| VibeVoice     | Mood / vibe transfer         |
| HiGGs Audio   | High-fidelity codec          |
| Step Audio    | Streaming low-latency        |

## First-Week Deliverables

- [ ] PerformanceManifest schema + tests
- [ ] Engine ABC + two reference adapters
- [ ] Axis router skeleton
- [ ] Bench harness vs. golden clips
- [ ] FastAPI render endpoint
- [ ] Voice registry (SQLite)
- [ ] CLI: `voice-prism render manifest.json`

## Quickstart

```
pip install -e .
pip install -e .[engines]
```

## Docs

Brainstorm and design notes: `.agents/brainstorm/`.
