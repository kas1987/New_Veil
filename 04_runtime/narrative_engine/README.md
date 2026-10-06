# ⚙️ MetaApp Narrative Engine (Testing Environment)

Welcome to the dedicated testing environment for the **Dynamic Narrative Engine**. This system acts as the bridge between your text inputs, the physical/emotional state of the character, the Large Language Model (Ollama), and the Audio TTS Voice parameters (SSML).

## 🧠 How the Architecture Works

The system does not just send raw text to an LLM. It acts as a **State Machine** that "branches" the narrative dynamically through the following loop:

1. **User Action & Intent Parsing**
   The user types an action (e.g., *"I pull you close"*). A heuristic (or NLP layer) analyzes the intent and determines the modifiers. *Does this increase intimacy? Does it decrease inhibition?*
2. **State Mutation (`CharacterState`)**
   The engine updates its internal state trackers (Arousal, Intimacy, Inhibition). These are clamped between 0-100.
3. **Context Injection (`DesireEngineLLM`)**
   Instead of a static system prompt, the engine rewrites the prompt every turn using `taxonomy/desire_engine.json`.
   *Example:* If Arousal hits 85, the prompt injected to Mistral includes `[SYSTEM: Current State - Arousal: 85, Inhibition: 20]`. This forces the LLM's weights to output fragmented, desperate text.
4. **LLM Inference**
   The local model (Mistral:7b) reads the injected state and the user prompt, then generates the dialogue.
5. **Audio SSML Branching (`AudioDirector`)**
   Once the text is generated, the engine checks the state against `taxonomy/audio_performance.json`. If Arousal > 80 and Inhibition < 30, it wraps the LLM's text in the `[heavy_breathing]` SSML tag, raising the pitch and altering the breath frequency.

### Branching to Variations

Branching occurs inherently because the **state dictates the prompt**.
* **Branch A (Slow Burn):** If the user chooses gentle actions, Arousal stays low while Intimacy rises. The AudioDirector selects the `[whisper_intimate]` SSML profile. The LLM generates slow, trusting dialogue.
* **Branch B (Aggressive):** If the user inputs harsh actions early, Inhibition might spike. The LLM shifts to defensive dialogue, and the Audio profile defaults or stutters.

## 🛠️ Dev Environment Files

* `core.py` - The main engine containing the State tracking, LLM interface, and Audio controller.
* `visual_director.py` - The async integration with ComfyUI.
* `cli_harness.py` - A dedicated console application to chat with the engine in isolation.

---

## ⚡ Vocal-First Async Architecture (Best Practice)

In the Meta App, it takes ~15+ seconds for ComfyUI to render an 8k ReActor image, but only ~2 seconds for Ollama to generate a vocal response.
To preserve immersion, this engine is built using a **Vocal-First Async Architecture**:

1. You type a message.
2. The Engine calculates the state and queries Ollama.
3. The Engine immediately routes the SSML payload back to the TTS app so the character speaks right away.
4. Concurrently, the `VisualDirector` spins up a **background thread** (`threading.Thread`) and silently pushes the modified prompt to ComfyUI.
5. You can continue talking to the character and hearing their voice.
6. When ComfyUI eventually finishes generating the frame in the background, a WebSocket quietly updates the Meta App UI with the new image.
*The image acts as an atmospheric correlation, but the Voice is the primary driver of real-time interaction.*

### Running the Test Harness

To evaluate changes to the taxonomies or the LLM, run:
```bash
python cli_harness.py
```
