import json
import logging
import os
import random
import sys
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from typing import Any

# ==========================================
# ⚙️ CONFIGURATION & BEST PRACTICES SETUP
# ==========================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("NarrativeEngine")

from narrative_engine.config import (
    AUDIO_OUT_DIR as _AUDIO_OUT_DIR,
)
from narrative_engine.config import (
    MODELS_DB as _MODELS_DB,
)
from narrative_engine.config import (
    SESSIONS_DIR as _SESSIONS_DIR,
)
from narrative_engine.config import (
    TAXONOMY_DIR as _TAXONOMY_DIR,
)
from narrative_engine.config import (
    TTS_SCRIPTS as _TTS_SCRIPTS,
)
from narrative_engine.config import (
    WORKSPACE_ROOT as _WORKSPACE_ROOT,
)

WORKSPACE_DIR = str(_WORKSPACE_ROOT)
TAXONOMY_DIR = str(_TAXONOMY_DIR)
TTS_SCRIPTS = str(_TTS_SCRIPTS)

# Put workspace root on path so character_voice_profiles is importable
if WORKSPACE_DIR not in sys.path:
    sys.path.insert(0, WORKSPACE_DIR)

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
# Fallback model; will attempt auto-detect if possible
DEFAULT_MODEL = "mistral:7b"


from narrative_engine.visual_director import VisualDirector


# ==========================================
# 🧠 DOMAIN MODELS
# ==========================================
@dataclass
class CharacterState:
    """Tracks the live emotional and physical state of the character."""

    arousal: int = 0
    inhibition: int = 60  # Starts relatively high
    intimacy: int = 10

    def clamp_values(self):
        """Ensures state values stay within 0-100 bounds."""
        self.arousal = max(0, min(100, self.arousal))
        self.inhibition = max(0, min(100, self.inhibition))
        self.intimacy = max(0, min(100, self.intimacy))

    def apply_stimulus(self, arousal_mod=0, inhibition_mod=0, intimacy_mod=0):
        """Applies modifiers based on narrative events."""
        self.arousal += arousal_mod
        self.inhibition += inhibition_mod
        self.intimacy += intimacy_mod
        self.clamp_values()

    def to_dict(self) -> dict[str, int]:
        return {"arousal": self.arousal, "inhibition": self.inhibition, "intimacy": self.intimacy}

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path: str) -> "CharacterState":
        from pathlib import Path as _Path

        p = _Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls(
            arousal=data.get("arousal", 0),
            inhibition=data.get("inhibition", 60),
            intimacy=data.get("intimacy", 10),
        )


# ==========================================
# 🎤 AUDIO / TTS MANAGER
# ==========================================
class ElevenLabsAudioDirector:
    """
    Drives ElevenLabs TTS with per-character, per-beat voice settings.

    Voice settings (stability / style / similarity_boost) are pulled from
    CHARACTER_VOICE_PROFILES via get_voice_for_beat(), so each beat of the
    arc sounds different — cold/controlled at L1, cracking at L4, fully
    unguarded at L8.
    """

    # Import lazily so the module can be used without TTS-Qwen on the path
    _SPEAK_TEXT: Any | None = None

    def __init__(self, tts_script_dir: str):
        """
        tts_script_dir: path to TTS-Qwen/scripts/ so speak_text can be imported.
        """
        self._tts_dir = tts_script_dir
        self._ensure_import()

    def _ensure_import(self) -> None:
        if ElevenLabsAudioDirector._SPEAK_TEXT is not None:
            return
        if self._tts_dir not in sys.path:
            sys.path.insert(0, self._tts_dir)
        try:
            from elevenlabs_tts import speak_text  # type: ignore

            ElevenLabsAudioDirector._SPEAK_TEXT = speak_text
            logger.info("ElevenLabs speak_text imported OK")
        except ImportError as e:
            logger.warning(f"Could not import speak_text: {e}. TTS calls will be skipped.")

    def speak(
        self,
        text: str,
        character_key: str,
        beat_number: int,
        output_path: str,
    ) -> str | None:
        """
        Synthesise *text* with the voice settings for this character at this beat.

        Returns the output path on success, None if TTS is unavailable or fails.

        The voice_settings injected here are the ones that make the voice
        actually change across the arc:
          beat 1  → stability ~0.62, style ~0.18  (cold, flat, controlled)
          beat 4  → stability ~0.44, style ~0.42  (cracking)
          beat 8  → stability ~0.24, style ~0.68  (fully unguarded)
        """
        if ElevenLabsAudioDirector._SPEAK_TEXT is None:
            logger.warning("speak_text unavailable — skipping TTS")
            return None

        # Resolve the current path so import works without changing cwd
        if self._tts_dir not in sys.path:
            sys.path.insert(0, self._tts_dir)

        # Pull voice_id + settings from character profile
        from scripts.generation.character_voice_profiles import get_voice_for_beat  # type: ignore

        params = get_voice_for_beat(character_key, beat_number)
        voice_id = params["voice_id"]
        settings = params["voice_settings"]

        if not voice_id:
            logger.warning(f"No voice_id for character '{character_key}' — skipping TTS")
            return None

        logger.info(
            f"TTS speak | char={character_key} beat={beat_number} "
            f"type={params['beat_type']} "
            f"stability={settings.get('stability')} style={settings.get('style')}"
        )

        try:
            out = ElevenLabsAudioDirector._SPEAK_TEXT(
                voice_id=voice_id,
                text=text,
                output=output_path,
                voice_settings=settings,
            )
            return str(out)
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None


# Keep the old class available for anything still referencing it
class AudioDirector:
    """Legacy SSML director — retained for backwards compatibility."""

    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = taxonomy_path

    def determine_voice_profile(self, state: "CharacterState") -> str:
        if state.arousal > 80 and state.inhibition < 30:
            return "heavy_breathing"
        elif state.intimacy > 60 and state.arousal < 50:
            return "whisper_intimate"
        elif state.inhibition < 40:
            return "submissive_pleading"
        return "default"

    def wrap_with_ssml(self, text: str, state: "CharacterState", voice_id: str = "en-US-JennyNeural") -> str:
        return f'<speak><voice name="{voice_id}">{text}</voice></speak>'


# ==========================================
# 🤖 LLM (OLLAMA) ORCHESTRATOR
# ==========================================
class DesireEngineLLM:
    """Handles communication with the local LLM, injecting state."""

    def __init__(self, taxonomy_path: str):
        self.taxonomy_path = taxonomy_path
        self.config: dict[str, Any] = self._load_taxonomy()
        self._char_prompts: dict[str, Any] = self._load_character_prompts()

    def _load_taxonomy(self) -> dict[str, Any]:
        """Loads the desire engine rules to formulate the system prompt."""
        path = os.path.join(self.taxonomy_path, "desire_engine.json")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load desire taxonomy from {path}: {e}")
            return {"ollama_system_prompts": {}}

    def _load_character_prompts(self) -> dict[str, Any]:
        """Loads per-character arc-state system prompts."""
        path = os.path.join(self.taxonomy_path, "character_system_prompts.json")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f).get("characters", {})
        except Exception as e:
            logger.warning(f"Could not load character system prompts from {path}: {e}")
            return {}

    def _resolve_arc_state(self, beat: int, arousal: int, character_key: str = None) -> str:
        """
        Map current beat + arousal to cold / breaking / warm.

        arc_type "cold_to_warm"    — cold until beat 3 or arousal 35
        arc_type "warm_to_inferno" — cold only at beat 1 AND arousal < 25 (Latin, Nigerian, etc.)
        """
        char = self._char_prompts.get(character_key or "", {})
        arc_type = char.get("arc_type", "cold_to_warm")

        if arc_type == "warm_to_inferno":
            if beat <= 1 and arousal < 25:
                return "cold"
            elif beat <= 4 and arousal < 70:
                return "breaking"
            return "warm"
        else:  # cold_to_warm (default)
            if beat <= 2 and arousal < 35:
                return "cold"
            elif beat <= 5 or arousal < 70:
                return "breaking"
            return "warm"

    def _pick_tease_directive(
        self, character_key: str, arc_state: str, last_tease_beat: int, current_beat: int
    ) -> str | None:
        """
        Maybe return a tease directive string for this turn.
        Rules:
          - Never fire two turns in a row (cooldown of 1 beat minimum)
          - Probability comes from the character+state config
          - Picks randomly from the directive list for that state
        Returns None if no tease this turn.
        """
        if current_beat - last_tease_beat < 2:
            return None

        char = self._char_prompts.get(character_key, {})
        state_data = char.get("arc_states", {}).get(arc_state, {})
        prob = state_data.get("tease_probability", 0.0)
        directives = state_data.get("tease_directives", [])

        if not directives or random.random() > prob:
            return None

        return random.choice(directives)

    @staticmethod
    def _format_history(history: "deque[tuple[str, str]]") -> str:
        """Format conversation history as a readable block for the LLM."""
        if not history:
            return ""
        lines = ["=== CONVERSATION SO FAR ==="]
        for role, text in history:
            label = "User" if role == "user" else "Character"
            lines.append(f"{label}: {text}")
        lines.append("=== END HISTORY ===")
        return "\n".join(lines)

    def build_character_system_prompt(self, character_key: str, beat: int, arousal: int) -> str:
        """
        Build the character-specific system prompt block for the current arc state.
        Returns empty string if character_key is unknown.
        """
        char = self._char_prompts.get(character_key)
        if not char:
            return ""

        arc_state = self._resolve_arc_state(beat, arousal, character_key)
        state_data = char.get("arc_states", {}).get(arc_state, {})
        rules = char.get("universal_rules", [])

        lines = [
            "=== CHARACTER PERSONA ===",
            char.get("identity", ""),
            "",
            "RULES (follow these absolutely):",
        ]
        for rule in rules:
            lines.append(f"- {rule}")

        lines += [
            "",
            f"=== CURRENT ARC STATE: {arc_state.upper()} ===",
            state_data.get("description", ""),
            "",
            f"VERBAL REGISTER: {state_data.get('verbal_register', '')}",
            "",
            "WHAT YOU DO:",
        ]
        for item in state_data.get("what_you_do", []):
            lines.append(f"- {item}")

        what_not = state_data.get("what_you_dont_do", [])
        if what_not:
            lines += ["", "WHAT YOU DON'T DO:"]
            for item in what_not:
                lines.append(f"- {item}")

        examples = state_data.get("example_phrases", [])
        if examples:
            lines += ["", "EXAMPLE PHRASES (tone reference, not scripts):"]
            for ex in examples:
                lines.append(f'  "{ex}"')

        dirty_style = state_data.get("dirty_talk_style", "")
        if dirty_style:
            lines += ["", f"DIRTY TALK STYLE: {dirty_style}"]

        # Bilingual escalation rules
        bilingual = char.get("bilingual_escalation", {})
        lang_rule = bilingual.get(arc_state, "")
        native_lang = char.get("native_language", {})
        if native_lang or lang_rule:
            lang_name = native_lang.get("name", "")
            llm_note = native_lang.get("llm_note", "")
            lines += ["", f"=== BILINGUAL REGISTER ({lang_name}) ==="]
            if llm_note:
                lines.append(llm_note)
            if lang_rule:
                lines.append(f"This arc state ({arc_state.upper()}): {lang_rule}")

        # Native phrases available for this state
        native_phrases = state_data.get("native_phrases", [])
        if native_phrases:
            lines += ["", "NATIVE PHRASES (use these or variations — format: phrase (pronunciation) (translation)):"]
            for ph in native_phrases:
                lines.append(f"  {ph}")

        lines += ["", "=== END PERSONA ==="]
        return "\n".join(lines)

    def fetch_model_metadata(self, db_path: str, model_name: str) -> dict[str, Any]:
        """Queries the master models.db and retrieves normalized metadata for the LLM persona."""
        import sqlite3

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT model_name, age, nationality, ethnicity, hair, bra_cup, bust, waist, hips, aurora_archetype, voice_preset, emotional_archetype FROM models WHERE model_name LIKE ? LIMIT 1",
                (f"%{model_name}%",),
            )
            row = cur.fetchone()
            conn.close()
            if row:
                return dict(row)
        except Exception as e:
            logger.error(f"Failed to fetch {model_name} from DB {db_path}: {e}")
        return {}

    def build_prompt(
        self,
        current_state: CharacterState,
        user_input: str,
        target_model: str = None,
        character_key: str = None,
        beat: int = 1,
        history: "deque[tuple[str, str]] | None" = None,
        tease_directive: str | None = None,
    ) -> str:
        """
        Constructs the full prompt for the LLM.

        Block order:
          1. Character arc persona (identity + arc state rules)
          2. DB physical metadata if target_model provided
          3. Live state numbers
          4. Conversation history (last N turns)
          5. Optional tease directive (injected just before the current user line)
          6. Current user input
        """
        parts: list[str] = []

        # 1. Character arc persona
        if character_key:
            char_block = self.build_character_system_prompt(character_key, beat, current_state.arousal)
            if char_block:
                parts.append(char_block)

        # 2. DB physical metadata
        if target_model:
            db_path = str(_MODELS_DB)
            meta = self.fetch_model_metadata(db_path, target_model)
            if meta:
                meta_str = (
                    f"You are playing the role of {meta.get('model_name', target_model)}. "
                    f"Physical traits: {meta.get('age', '')}, {meta.get('ethnicity', '')} "
                    f"with {meta.get('hair', '')} hair. "
                    f"Body type: {meta.get('aurora_archetype', 'Curvy')} "
                    f"({meta.get('bust', '')}-{meta.get('waist', '')}-{meta.get('hips', '')})."
                )
                parts.append(meta_str)

        # 3. Live state numbers
        prompts = self.config.get("ollama_system_prompts", {})
        if not parts:
            parts.append(prompts.get("base_persona", "You are an interactive narrative AI."))

        template = prompts.get(
            "state_injection_template",
            "[SYSTEM: Current State - Arousal: {{arousal}}, Inhibition: {{inhibition}}, Intimacy: {{intimacy}}. Adjust character dialogue and narration accordingly.]",
        )
        state_str = (
            template.replace("{{arousal}}", str(current_state.arousal))
            .replace("{{inhibition}}", str(current_state.inhibition))
            .replace("{{intimacy}}", str(current_state.intimacy))
        )
        parts.append(state_str)

        system_block = "\n\n".join(parts)

        # 4. Conversation history — placed after the system block, before current turn
        history_block = self._format_history(history) if history else ""

        # 5. Optional tease directive — a one-line instruction inserted just before
        #    the user line so the LLM acts on it immediately
        tease_block = ""
        if tease_directive:
            tease_block = f"[TEASE DIRECTIVE: {tease_directive}]\n"

        # 6. Assemble: system | history | tease | current exchange
        if history_block:
            return f"{system_block}\n\n{history_block}\n\n{tease_block}User: {user_input}\nCharacter:"
        return f"{system_block}\n\n{tease_block}User: {user_input}\nCharacter:"

    def generate(self, prompt: str, model: str = DEFAULT_MODEL) -> str:
        """Calls the local Ollama instance. Falls back to Mock if unreachable."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"stop": ["\nUser:", "User:", "User: "]},
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=(60 if model == DEFAULT_MODEL else 10)) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()
        except (urllib.error.URLError, TimeoutError) as e:
            logger.error(f"Ollama connection failed: {e}. Returning simulated MOCK response.")
            return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Provides a safe fallback response for testing logic when Ollama is offline."""
        if "arousal: 80" in prompt or "arousal: 100" in prompt:
            return "I can't... I can't think straight. Please don't stop."
        elif "intimacy: " in prompt and "inhibition: 60" in prompt:
            return "You're making me blush. We shouldn't be so loud here."
        else:
            return "I feel my pulse racing as you do that..."


# ==========================================
# 🎮 MAIN APPLICATION LOOP
# ==========================================
class InteractiveNarrativeEngine:
    """The master controller tying State, Audio, and LLM together."""

    # Rolling history window — last N exchanges kept in context
    HISTORY_MAX = 8

    def __init__(
        self,
        target_model: str = None,
        character_key: str = None,
        history_max: int = HISTORY_MAX,
        audio_output_dir: str = None,
        session_id: str = None,
        taxonomy_dir: str = None,
        audio_out_dir: str = None,
    ):
        import uuid as _uuid
        from pathlib import Path as _Path

        _tax = taxonomy_dir or TAXONOMY_DIR
        self.state = CharacterState()
        try:
            from narrative_engine.voice_prism_director import VoicePrismAudioDirector

            self.tts = VoicePrismAudioDirector()
        except Exception as _e:
            logger.warning(f"VoicePrismAudioDirector unavailable, falling back to ElevenLabs: {_e}")
            self.tts = ElevenLabsAudioDirector(TTS_SCRIPTS)
        self.audio_director = AudioDirector(_tax)  # kept for legacy callers
        self.visual_director = VisualDirector()
        self.llm = DesireEngineLLM(_tax)
        self.target_model = target_model
        self.character_key = character_key  # e.g. "russian", "japanese", "latin"
        self._character_key = character_key  # alias used by server
        self.beat = 1
        self._beat = 1  # alias used by server
        self._last_tease_beat = -99
        self._history: deque[tuple[str, str]] = deque(maxlen=history_max)
        self._audio_out_dir = audio_out_dir or audio_output_dir or str(_AUDIO_OUT_DIR)

        # Session persistence
        self._session_id = session_id or str(_uuid.uuid4())
        self._session_dir = _Path(str(_SESSIONS_DIR)) / self._session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)
        self._state_path = str(self._session_dir / "state.json")
        self._history_path = str(self._session_dir / "history.json")
        self._load_session()

    def _save_session(self) -> None:
        self.state.save(self._state_path)
        with open(self._history_path, "w", encoding="utf-8") as f:
            json.dump(list(self._history), f, ensure_ascii=False)

    def _load_session(self) -> None:
        from pathlib import Path as _Path

        self.state = CharacterState.load(self._state_path)
        hp = _Path(self._history_path)
        if hp.exists():
            pairs = json.loads(hp.read_text(encoding="utf-8"))
            self._history = deque(pairs, maxlen=self.HISTORY_MAX)

    def process_turn(
        self,
        user_action_text: str = None,
        user_input: str = None,
        arousal_mod=0,
        inhibition_mod=0,
        intimacy_mod=0,
        character_key: str = None,
        beat: int = None,
    ):
        # normalise params — support both old positional and new keyword forms
        text = user_action_text or user_input or ""
        if character_key:
            self.character_key = character_key
            self._character_key = character_key
        if beat is not None:
            self.beat = beat
            self._beat = beat

        logger.info(f"--- TURN START (beat={self.beat}, char={self.character_key}) ---")
        logger.info(f"User Action: '{text}'")

        # 1. Update state
        self.state.apply_stimulus(arousal_mod, inhibition_mod, intimacy_mod)
        logger.info(f"New State -> {self.state.to_dict()}")

        # 2. Maybe fire a tease directive this turn
        arc_state = self.llm._resolve_arc_state(self.beat, self.state.arousal, self.character_key or "")
        tease = self.llm._pick_tease_directive(
            self.character_key or "",
            arc_state,
            self._last_tease_beat,
            self.beat,
        )
        if tease:
            self._last_tease_beat = self.beat
            logger.info(f"Tease fired (state={arc_state}): {tease[:60]}...")

        # 3. Build prompt with history + optional tease
        prompt = self.llm.build_prompt(
            self.state,
            text,
            target_model=self.target_model,
            character_key=self.character_key,
            beat=self.beat,
            history=self._history if self._history else None,
            tease_directive=tease,
        )
        logger.debug(f"Computed LLM Prompt:\n{prompt}")
        self.beat += 1

        raw_response = self.llm.generate(prompt)
        logger.info(f"LLM Raw Text: '{raw_response}'")

        # 4. Store exchange in rolling history
        self._history.append(("user", text))
        self._history.append(("character", raw_response))

        # 5. Speak with ElevenLabs — voice settings match current beat
        audio_path: str | None = None
        if self.character_key and raw_response:
            filename = f"{self.character_key}_beat{self.beat - 1:02d}.wav"
            output_path = os.path.join(self._audio_out_dir, filename)
            audio_path = self.tts.speak(
                text=raw_response,
                character_key=self.character_key,
                beat_number=self.beat - 1,  # beat was already incremented above
                output_path=output_path,
            )
            if audio_path:
                logger.info(f"Audio saved: {audio_path}")

        # 6. Visual generation via ReActor
        if self.target_model:
            self.visual_director.generate_image_from_state(self.state, raw_response, self.target_model)

        # 7. Persist session state + history
        self._beat = self.beat
        self._save_session()

        return raw_response, audio_path


if __name__ == "__main__":
    logger.info("Initializing Narrative Engine Pipeline...")
    engine = InteractiveNarrativeEngine()

    # ------------------ SIMULATION MODE ------------------
    print("\n" + "=" * 50)
    print("🎬 MODULE TEST: SIMULATING PROGRESSION")
    print("For interactive mode, run cli_harness.py instead.")
    print("=" * 50 + "\n")

    try:
        # Turn 1: Gentle Introduction
        print("=" * 50 + "\n")

        # Turn 1: Gentle Introduction
        engine.process_turn(
            "I gently stroke your cheek and whisper a compliment.", arousal_mod=10, intimacy_mod=20, inhibition_mod=-5
        )

        # Turn 2: Escalation
        engine.process_turn(
            "I lock the bedroom door, dim the lights, and pull you close.",
            arousal_mod=30,
            intimacy_mod=15,
            inhibition_mod=-15,
        )

        # Turn 3: Peak Intensity
        engine.process_turn(
            "I push you onto the bed, staring deeply into your eyes without holding back.",
            arousal_mod=45,
            intimacy_mod=10,
            inhibition_mod=-20,
        )

        print("=" * 50)
        print("✅ Pipeline simulation completed successfully.")
    except KeyboardInterrupt:
        print("\nExiting engine.")
