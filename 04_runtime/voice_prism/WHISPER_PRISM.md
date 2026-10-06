# whisper-agent

Real-time Whisper transcription with wake-word gating, optimized for Bluetooth
mics (Meta / Ray-Ban Smart Glasses in Hands-Free mode).

## Pipeline

```
Glasses Mic
  -> Windows Bluetooth Hands-Free input
  -> sounddevice RawInputStream (16 kHz int16)
  -> WebRTC VAD (utterance segmentation)
  -> faster-whisper transcribe
  -> wake-word match
  -> command capture window
  -> pipeline.handle_command(command, ctx)
```

## Install

```powershell
pip install -r requirements.txt
```

CUDA users: `faster-whisper` will auto-pick `device="auto"`. Override
`compute_type` in `wake_config.json` (`int8`, `int8_float16`, `float16`).

## Find your mic

```powershell
python listener.py --list-devices
```

Pick the row whose name matches your glasses (e.g. `Headset Microphone (Ray-Ban Meta)`).

## Run

```powershell
python listener.py --device 3
```

Override wake words inline:

```powershell
python listener.py --device 3 --wake "hey opal" "computer"
```

Override model:

```powershell
python listener.py --device 3 --model small.en
```

## Wake words

Edit `wake_config.json` to change defaults. Default set:

- `hey mirror`
- `okay mirror`
- `hey whisper`
- `computer`

If the wake word is followed by speech in the same utterance (`"computer, what's the weather"`),
the trailing text is dispatched immediately. Otherwise the listener opens a
`post_wake_listen_ms` window (default 6 s) and dispatches the next utterance.

## Wiring into your AI stack

Edit `pipeline.py`. Two extension points:

**1. Register pattern handlers** (regex, first match wins):

```python
from pipeline import register, CommandContext

def open_browser(cmd: str, ctx: CommandContext) -> None:
    ...

register(r"\b(open|launch)\s+browser\b", open_browser)
```

**2. Replace the default handler** in `pipeline._default` to fan out to:

- Intent parser (rasa, regex, LLM)
- XTTS / TTS reply
- n8n webhook (`requests.post(...)`)
- Local LLM (Ollama, llama.cpp HTTP)

## Tuning notes

| Setting | Effect |
|---|---|
| `vad_aggressiveness` (0-3) | Higher = stricter speech gate. 2 is a good Bluetooth default. |
| `silence_timeout_ms` | How long to wait before closing an utterance. 800 ms feels natural. |
| `post_wake_listen_ms` | Command window after a bare wake word. 6 s is generous. |
| `model` | `tiny.en` (fastest), `base.en`, `small.en`, `medium.en`. `base.en` int8 runs on CPU. |

## Bluetooth caveats

- Use **Hands-Free / HFP** profile (mono 8-16 kHz). A2DP can't carry mic audio.
- Don't route playback to the glasses while listening — Windows downgrades both
  channels and Whisper accuracy collapses. Keep output on speakers / a separate
  device.
- Stay within ~5-10 ft for stable HFP.

## Layout

```
whisper-agent/
├── listener.py        # mic capture + VAD + Whisper + wake-word loop
├── pipeline.py        # command dispatch + handler registry
├── wake_config.json   # tunable defaults
├── requirements.txt
└── README.md
```
