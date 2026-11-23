---
status: accepted
---

# Deterministic Posture Evaluation for Resonance Over LLM Scoring

Resonance progression and degradation are evaluated deterministically from conversational posture (`evaluate_talk_resonance`) rather than by prompting an LLM to assign a numeric score. LLMs remain reserved for character voice and live narrative generation (`llm_provider.py`), downstream of the alignment scorer.

## Considered Options

- **LLM-judged scoring:** Non-deterministic across models and runs, vulnerable to prompt injection, adds turn latency to sensory HUD cues, and makes multi-turn psychometric calibration noisy.
- **Keyword counting:** Easily exploited by dumping lore nouns (`veil`, `quasar`, `prism`) without genuine engagement.

## Consequences

- Keyword dumps and command spamming trigger deterministic friction penalties instead of positive gains.
- Psychometric calibration and regression testing are completely reproducible without live inference.
- Narrative phrasing outside explicit posture patterns relies on authorable rules rather than latent semantic grading, which must be weighted cleanly per character over time.
