"""Embedding-based semantic scorer — augments lexical signal with similarity.

Uses Ollama's `nomic-embed-text` (or any embed model) to compute cosine
similarity between agent output and pre-defined canonical reference texts
for each axis: Prism resonance, Dark Quasar resonance, emotional depth.

Reference vectors are computed lazily on first call and cached in-process.
Falls back to a no-op (returns None) if Ollama is unreachable, so callers
can detect absence and stay on lexical-only.

Wired pattern:
    sem = semantic_scorer.SemanticScorer()
    sig = sem.score("Whispers cling to the edges of the veil...")
    # sig = {"prism": 0.42, "dark_quasar": 0.78, "depth": 0.63} or None
"""

from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("VEIL_EMBED_MODEL", "nomic-embed-text")
EMBED_TIMEOUT = float(os.environ.get("VEIL_EMBED_TIMEOUT", "15"))


# Canonical reference texts — anchors for each axis. Multiple per axis;
# average vector is used as the reference.
_PRISM_REFS = [
    "Warmth and gentle guidance. A lantern in the dawn, a soft welcome, the beauty that invites without conditions.",
    "Bright light, kindness, surface clarity, the candle that holds back the dark, the promise of safety.",
    "Prism resonance: radiant, beautiful, openly readable, welcoming, the world made visible.",
]
_DQ_REFS = [
    "Hidden weight, gravitational truth, the dark beneath the surface, the buried thing that ages everything.",
    "Shadows that have shape. The cost of seeing. Ash where memory used to be. The void door that should not exist.",
    "Dark Quasar: dangerous, transformative, the truth that costs, the depth that is not safe.",
]
_DEPTH_REFS = [
    "Memory and emotion that ache. The dream that almost reveals. Symbolic resonance. The story that lives in stories.",
    "Whispers, echoes, the thread between selves. Felt longing, remembered loss, the mirror that lingers.",
    "Emotional depth: the quality of feeling that earns deeper truth. Not described, embodied.",
]


def _ollama_embed(text: str, model: str = EMBED_MODEL) -> list[float] | None:
    """Call /api/embeddings; return embedding vector or None on failure."""
    body = json.dumps({"model": model, "prompt": text}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=EMBED_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        emb = data.get("embedding")
        if isinstance(emb, list) and emb:
            return [float(x) for x in emb]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _mean_vector(vecs: list[list[float]]) -> list[float]:
    if not vecs:
        return []
    dim = len(vecs[0])
    out = [0.0] * dim
    for v in vecs:
        for i in range(dim):
            out[i] += v[i]
    n = float(len(vecs))
    return [x / n for x in out]


class SemanticScorer:
    """Cosine-similarity scorer against averaged reference vectors per axis.

    Designed to be cheap to construct; reference vectors are computed lazily
    on first score() call and cached for the process lifetime.
    """

    def __init__(self, model: str = EMBED_MODEL) -> None:
        self.model = model
        self._refs: dict[str, list[float]] = {}
        self._unavailable = False

    def _ensure_refs(self) -> bool:
        if self._unavailable:
            return False
        if self._refs:
            return True
        for axis, texts in (
            ("prism", _PRISM_REFS),
            ("dark_quasar", _DQ_REFS),
            ("depth", _DEPTH_REFS),
        ):
            vecs = []
            for t in texts:
                e = _ollama_embed(t, self.model)
                if e is None:
                    self._unavailable = True
                    self._refs = {}
                    return False
                vecs.append(e)
            self._refs[axis] = _mean_vector(vecs)
        return True

    def score(self, text: str) -> dict[str, float] | None:
        """Return {axis: similarity 0-1} or None if Ollama is unreachable.

        Similarities are clamped to [0, 1] for the runtime convention;
        raw cosine can be negative for orthogonal/opposing semantics.
        """
        if not text or not text.strip():
            return None
        if not self._ensure_refs():
            return None
        emb = _ollama_embed(text, self.model)
        if emb is None:
            return None
        out: dict[str, float] = {}
        for axis, ref in self._refs.items():
            sim = _cosine(emb, ref)
            out[axis] = max(0.0, min(1.0, sim))
        return out


if __name__ == "__main__":
    import sys

    sample = " ".join(sys.argv[1:]) or (
        "The lanterns of Veil Town flicker like secrets in the dark, "
        "and shadows whisper of forgotten memories."
    )
    s = SemanticScorer()
    result = s.score(sample)
    print(json.dumps({"input": sample, "score": result}, indent=2))
