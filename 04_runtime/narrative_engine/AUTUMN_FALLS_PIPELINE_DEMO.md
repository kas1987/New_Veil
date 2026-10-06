# 🍁 Complete Pipeline Demo: "Autumn Falls"

This document demonstrates how our three entirely separate systems—**The Narrative Engine (Ollama)**, **The Voice (TTS/SSML)**, and **The Visuals (ComfyUI + ReActor)**—sync together to create a seamless, branching interactive experience using Autumn Falls as the target persona.

## 1. Character Setup & Initialization

Before the session starts, the system registers Autumn's profile across the three pillars:
*   **LLM Persona (Desire Engine):** *"You are Autumn. You are confident, playful, but highly responsive to physical touch."*
*   **Audio Profile:** `en-US-JennyNeural` (or a cloned voice model of Autumn), mapped to our `audio_performance.json` rules.
*   **Visual Anchor:** ComfyUI is loaded with a base model (e.g., `UberRealisticPornMerge`) and ReActor is primed with `autumn_falls_face.safetensors`.

---

## 🎬 Turn 1: The Setup (Low Arousal, Building Intimacy)

**You Type:** *"I pour you a glass of wine, sit next to you on the couch, and gently stroke your hair."*

### Step 1: Narrative Engine (Ollama)
The engine parses the intent and mutates the state:
*   `Arousal:` 15
*   `Intimacy:` 35
*   `Inhibition:` 45
*   *Prompt Injected to Mistral:* `[Current State - Arousal: 15. Keep responses warm and conversational.]`
*   *LLM Output:* "Mmm, thank you. You always know exactly how to relax me after a long day."

### Step 2: Audio Engine (TTS)
The engine checks the state numbers against `audio_performance.json`. Arousal is low, Intimacy is climbing.
*   *Audio Tag Selected:* `[whisper_intimate]`
*   *SSML Output sent to TTS:*
    ```xml
    <speak><voice name="autumn_clone_v1">
      <prosody volume="-6dB" rate="slow" pitch="low">Mmm, thank you. You always know exactly how to relax me after a long day.</prosody>
    </voice></speak>
    ```

### Step 3: Visual Engine (ComfyUI + ReActor)
Because arousal is low, the image prompt is generated for relaxed framing.
*   **Positive Prompt:** `1girl, sitting on couch, holding wine glass, relaxed smile, gentle lighting, medium shot, high quality, highly detailed`
*   **ReActor Action:** Generates a random realistic girl on a couch, then flawlessly maps `autumn_falls_face.safetensors` onto the face.
*   *Result:* Autumn is sitting next to you, looking relaxed and identical to the real person.

---

## 🎬 Turn 2: The Escalation (Branching the State)

**You Type:** *"I take the glass from your hand, set it down, and kiss your neck, trailing my hands down your thighs."*

### Step 1: Narrative Engine (Ollama)
The system detects an aggressive escalation in physical touch. State mutates drastically:
*   `Arousal:` 65 *(Huge jump)*
*   `Intimacy:` 50
*   `Inhibition:` 25 *(Dropping fast)*
*   *Prompt Injected to Mistral:* `[Current State - Arousal: 65, Inhibition: 25. Responses should be shorter, reactive, losing train of thought.]`
*   *LLM Output:* "Wait... oh... wow. I... I wasn't expecting that so fast, but please... keep going..."

### Step 2: Audio Engine (TTS)
Arousal crossed 60, Inhibition dropped below 30. The audio rules shift the delivery dynamically without you having to code anything.
*   *Audio Tag Selected:* `[submissive_pleading]` with an added breath cue.
*   *SSML Output sent to TTS:*
    ```xml
    [sharp_inhale]
    <speak><voice name="autumn_clone_v1">
      <prosody volume="-2dB" rate="medium" pitch="+2st"><emphasis level="moderate">Wait... oh... wow. I... I wasn't expecting that so fast, but please... keep going...</emphasis></prosody>
    </voice></speak>
    ```

### Step 3: Visual Engine (ComfyUI + ReActor)
The image generation prompt dynamically injects visual modifiers based on the new `Arousal (65)` state (e.g., adding flush, parted lips, tighter framing).
*   **Dynamic Prompt Injection:** `(flushed skin:1.2)`, `(parted lips:1.1)`, `heavy breathing`, `POV angle`
*   **Positive Prompt:** `POV, looking down at 1girl, head tilted back, kissing neck, (flushed skin:1.2), (parted lips:1.1), highly detailed, 8k`
*   **ReActor Action:** ReActor takes this new POV angle with tilted geometry, maps the anchor points, and applies `autumn_falls_face.safetensors`.
*   *Result:* The framing shifts to a POV angle. The generated face has flushed skin and parted lips (matching the AI's dialogue), and ReActor guarantees it still strictly looks exactly like Autumn Falls despite the extreme change in character posture.

---

## The Workflow Recap
By treating the **Narrative State** as the ultimate source of truth, everything branches together automatically. 
You don't have to tell the image generator to give her *"flushed skin"* or tell the TTS to *"sound breathy"*. You just chat. The Engine adjusts the **State Numbers**, and those numbers tell Mistral to change its dialogue, tell ComfyUI to change its visual prompts, and tell the Audio router to change the SSML tags. And through it all, **ReActor** acts as the visual anchor, ensuring that no matter what the LLM hallucinates or what pose the prompt generates, the face mapped on top is always perfectly Autumn.