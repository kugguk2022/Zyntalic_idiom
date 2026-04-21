"""
Transformer-based engine for Zyntalic.
Uses sentence-transformers to find the closest "Schelling point" in the anchor space.
"""
import os

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

_MODEL = None
_MODEL_ATTEMPTED = False
_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_MODEL_NAME = os.getenv("ZYNTALIC_EMBEDDING_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL
_MODEL_ALIASES = {
    "all-minilm-l6-v2": "all-MiniLM-L6-v2",
    "minilm": "all-MiniLM-L6-v2",
    "mini-lm": "all-MiniLM-L6-v2",
    "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5",
    "bge-small": "BAAI/bge-small-en-v1.5",
}

from . import core  # noqa: E402


def get_model():
    global _MODEL, _MODEL_ATTEMPTED, SentenceTransformer

    # Lazy import if not already imported (though we check module availability above)
    if SentenceTransformer is None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None

    if _MODEL is None and not _MODEL_ATTEMPTED:
        try:
            _MODEL_ATTEMPTED = True
            # resilient, lightweight model
            name = _MODEL_ALIASES.get(_MODEL_NAME.lower(), _MODEL_NAME)
            try:
                _MODEL = SentenceTransformer(name)
            except Exception:
                if name != _DEFAULT_MODEL:
                    _MODEL = SentenceTransformer(_DEFAULT_MODEL)
                else:
                    raise
        except Exception:
            _MODEL = None

    return _MODEL

def get_anchor_embeddings():
    """
    Compute or retrieve embeddings for all Zyntalic anchors.
    This is a simplified approach: we just embed the anchor names themselves
    to find semantic matches.
    """
    # Get all anchors from the core logic
    # In core.py, anchors are keys in core.ANCHOR_VECS or we can inspect lexicons
    # For this MVP, we'll extract them from the simplified ANCHOR_VECS keys if available
    # or just use a hardcoded list of known anchors for stability if core doesn't expose them cleanly.

    # Let's inspect core internals if possible, or fall back to standard ones.
    # Let's inspect core internals if possible, or fall back to standard ones.
    # core.ANCHOR_VECS was removed in favor of lazy loading.
    try:
        if hasattr(core, "_get_anchor_vecs"):
            return list(core._get_anchor_vecs().keys())
        # Fallback if core logic changes again
        if hasattr(core, "ANCHORS"):
            return core.ANCHORS
    except Exception:
        pass

    return ["Homer_Iliad", "Plato_Republic"] # Minimal fallback

def semantic_match(text: str, top_k: int = 3) -> list[str]:
    """
    Find the top_k anchors that semantically match the input text.
    """
    model = get_model()
    if model is None:
        return []

    anchors = get_anchor_embeddings()
    if not anchors:
        return []

    # Encode input and anchors
    # Check if we can cache anchor embeddings for performance
    # For now, we compute on the fly (small list) or use cached

    # We will use a simple cache on the module level if this scales
    # But for a few dozen anchors, it's fast.

    encoded_input = model.encode(text)
    encoded_anchors = model.encode(anchors)

    # Cosine similarity
    sims = np.dot(encoded_anchors, encoded_input) / (
        np.linalg.norm(encoded_anchors, axis=1) * np.linalg.norm(encoded_input)
    )

    # Get top k indices
    top_indices = np.argsort(sims)[-top_k:][::-1]

    return [anchors[i] for i in top_indices]

def translate_transformer(text: str, mirror_rate: float = 0.8) -> str:
    """
    Translate text using semantic anchor matching.
    Instead of random or heuristic anchors, we use the ones that match the *meaning* of the input.
    """
    # 1. Find semantic anchors
    matched_anchors = semantic_match(text, top_k=2)

    # 2. Assign weights (simple decay)
    weights = [0.7, 0.3] if len(matched_anchors) >= 2 else [1.0]

    # 3. Use core logic to generate sentence with these FORCED anchors
    # We need a way to pass specific anchors to generate_entry or plain_sentence_anchored
    # core.generate_entry calls plain_sentence_anchored internally with random selection
    # We might need to call lower-level functions or monkey-patch

    # Better approach: Use core.plain_sentence_anchored directly
    # but we need a 'rng'
    from .utils.rng import get_rng
    rng = get_rng(text) # deterministic based on input

    if not matched_anchors:
        # Fallback to core default
        entry = core.generate_entry(text, mirror_rate=mirror_rate)
        return entry['sentence']

    sentence = core.plain_sentence_anchored(rng, matched_anchors, weights)

    # Post-processing (Context tail etc) happens in generate_entry usually
    # Let's replicate the minimal needed flow or re-use core.make_context if needed.
    # core.generate_entry does:
    #   1. anchors = ...
    #   2. sentence = plain_sentence_anchored(...)
    #   3. ctx = make_context(...)
    #   4. return sentence + " " + ctx

    # We can reuse general structure

    # For simplicity, let's just return the sentence part + a standard tail
    # Or properly construct it.

    # Let's see if we can just call `core.generate_entry` but force anchors?
    # core.generate_entry does not accept anchors argument.

    # We will reimplement the composition logic here using the public helpers from core
    # to ensure we get the high-quality output but with OUR anchors.

    lemma = core.lemmatize(text.split()[0]) if text else "void"
    ctx = core.make_context(text, lemma, matched_anchors, "noun")

    return f"{sentence} {ctx}"
