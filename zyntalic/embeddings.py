# -*- coding: utf-8 -*-
"""
Embedding backend for Zyntalic.

- If `sentence-transformers` is installed, we use a small model.
- Otherwise we fall back to deterministic hash-based pseudo-embeddings.

This keeps the repo runnable in offline/minimal environments while still allowing
a better backend when you want it.
"""

from __future__ import annotations

from typing import List, Optional
import hashlib
import os
import random

_MODEL = None
_DIM: Optional[int] = None

# When set, skip loading sentence-transformers and use fast hash-based embeddings only.
_HASH_ONLY = os.getenv("ZYNTALIC_FAST", "").lower() in ("1", "true", "yes", "on") or os.getenv("ZYNTALIC_HASH_ONLY", "").lower() in ("1", "true", "yes", "on")

def _lazy_load_model() -> None:
    global _MODEL, _DIM
    if _MODEL is not None:
        return
    if _HASH_ONLY:
        _MODEL = None
        _DIM = None
        return
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        _DIM = int(_MODEL.get_sentence_embedding_dimension())
    except Exception:
        _MODEL = None
        _DIM = None


def embed_text(text: str, dim: int = 300) -> List[float]:
    """
    Return a deterministic embedding vector of length `dim`.

    If a sentence-transformers model is available, we take its embedding and
    deterministically trim/pad to `dim`. Otherwise we generate a stable
    pseudo-embedding using a hash-seeded RNG.

    Set ZYNTALIC_FAST=1 (or ZYNTALIC_HASH_ONLY=1) to force the fast hash-only
    path, avoiding model load for lower latency on long texts.
    """
    _lazy_load_model()

    if _MODEL is not None:
        try:
            v = _MODEL.encode([text or ""], normalize_embeddings=True)[0].tolist()
            if len(v) >= dim:
                return v[:dim]
            # pad deterministically based on text
            seed = int(hashlib.blake2b((text or "").encode("utf-8"), digest_size=8).hexdigest(), 16)
            rng = random.Random(seed)
            return v + [rng.random() for _ in range(dim - len(v))]
        except Exception:
            # fall through to hash embedding
            pass

    data = (text or "").encode("utf-8")
    seed = int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")
    rng = random.Random(seed)
    return [rng.random() for _ in range(dim)]
