# -*- coding: utf-8 -*-
"""
Embedding backend for Zyntalic.

- If `sentence-transformers` is installed, we use a small model.
- Otherwise we fall back to deterministic hash-based pseudo-embeddings.
  Choose the model via `ZYNTALIC_EMBEDDING_MODEL` (default: all-MiniLM-L6-v2).

This keeps the repo runnable in offline/minimal environments while still allowing
a better backend when you want it.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import atexit
import hashlib
import json
import os
import random
import threading
from pathlib import Path

_MODEL = None
_DIM: Optional[int] = None

_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_MODEL_NAME = os.getenv("ZYNTALIC_EMBEDDING_MODEL", _DEFAULT_MODEL).strip() or _DEFAULT_MODEL

_MODEL_ALIASES = {
    "all-minilm-l6-v2": "all-MiniLM-L6-v2",
    "minilm": "all-MiniLM-L6-v2",
    "mini-lm": "all-MiniLM-L6-v2",
    "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5",
    "bge-small": "BAAI/bge-small-en-v1.5",
}


def _resolve_model_name(name: str) -> str:
    if not name:
        return _DEFAULT_MODEL
    key = name.strip()
    lower = key.lower()
    return _MODEL_ALIASES.get(lower, key)

# When set, skip loading sentence-transformers and use fast hash-based embeddings only.
_HASH_ONLY = os.getenv("ZYNTALIC_FAST", "").lower() in ("1", "true", "yes", "on") or os.getenv("ZYNTALIC_HASH_ONLY", "").lower() in ("1", "true", "yes", "on")

# Disk-backed embedding caches to keep runs stable and fast.
_CACHE_ENABLED = os.getenv("ZYNTALIC_EMBED_CACHE", "").lower() not in ("0", "false", "no", "off")
_CACHE_FLUSH_EVERY = int(os.getenv("ZYNTALIC_EMBED_CACHE_FLUSH", "50"))

_CACHE_LOCK = threading.Lock()
_CACHE_LOADED = False
_WORD2VEC: Dict[str, List[float]] = {}
_CONTEXT2VEC: Dict[str, List[float]] = {}
_WORD_DIRTY = 0
_CONTEXT_DIRTY = 0

_ROOT_DIR = Path(__file__).resolve().parents[2]
_CACHE_DIR = _ROOT_DIR / "data" / "cache"
_WORD_CACHE_PATH = _CACHE_DIR / "word2vector.json"
_CONTEXT_CACHE_PATH = _CACHE_DIR / "context2vector.json"


def _ensure_cache_dir() -> None:
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _load_cache() -> None:
    global _CACHE_LOADED, _WORD2VEC, _CONTEXT2VEC
    if _CACHE_LOADED or not _CACHE_ENABLED:
        return
    _ensure_cache_dir()
    for path, target in ((_WORD_CACHE_PATH, "_WORD2VEC"), (_CONTEXT_CACHE_PATH, "_CONTEXT2VEC")):
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if target == "_WORD2VEC":
                    _WORD2VEC = data
                else:
                    _CONTEXT2VEC = data
        except Exception:
            # Ignore corrupt or unreadable cache files.
            continue
    _CACHE_LOADED = True


def _write_cache(path: Path, payload: Dict[str, List[float]]) -> None:
    _ensure_cache_dir()
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True)
        tmp_path.replace(path)
    except Exception:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except Exception:
            pass


def _flush_cache(force: bool = False) -> None:
    global _WORD_DIRTY, _CONTEXT_DIRTY
    if not _CACHE_ENABLED:
        return
    if force or _WORD_DIRTY >= _CACHE_FLUSH_EVERY:
        _write_cache(_WORD_CACHE_PATH, _WORD2VEC)
        _WORD_DIRTY = 0
    if force or _CONTEXT_DIRTY >= _CACHE_FLUSH_EVERY:
        _write_cache(_CONTEXT_CACHE_PATH, _CONTEXT2VEC)
        _CONTEXT_DIRTY = 0


def _cache_key(text: str, dim: int) -> str:
    return f"{dim}::{text}"


def _cache_bucket(text: str) -> Dict[str, List[float]]:
    # Single token (no whitespace) -> word2vector, otherwise context2vector.
    return _WORD2VEC if (text and not any(ch.isspace() for ch in text)) else _CONTEXT2VEC


def _get_cached_vector(text: str, dim: int) -> Optional[List[float]]:
    if not _CACHE_ENABLED:
        return None
    _load_cache()
    key = _cache_key(text, dim)
    bucket = _cache_bucket(text)
    vec = bucket.get(key)
    if isinstance(vec, list) and len(vec) == dim:
        return vec
    return None


def _store_cached_vector(text: str, dim: int, vec: List[float]) -> None:
    global _WORD_DIRTY, _CONTEXT_DIRTY
    if not _CACHE_ENABLED:
        return
    _load_cache()
    key = _cache_key(text, dim)
    bucket = _cache_bucket(text)
    if key in bucket:
        return
    bucket[key] = vec
    if bucket is _WORD2VEC:
        _WORD_DIRTY += 1
    else:
        _CONTEXT_DIRTY += 1
    _flush_cache()


atexit.register(lambda: _flush_cache(force=True))

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
        model_name = _resolve_model_name(_MODEL_NAME)
        try:
            _MODEL = SentenceTransformer(model_name)
        except Exception:
            if model_name != _DEFAULT_MODEL:
                _MODEL = SentenceTransformer(_DEFAULT_MODEL)
            else:
                raise
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
    normalized = (text or "").strip()
    with _CACHE_LOCK:
        cached = _get_cached_vector(normalized, dim)
    if cached is not None:
        return cached

    if _MODEL is not None:
        try:
            v = _MODEL.encode([normalized], normalize_embeddings=True)[0].tolist()
            if len(v) >= dim:
                out = v[:dim]
                with _CACHE_LOCK:
                    _store_cached_vector(normalized, dim, out)
                return out
            # pad deterministically based on text
            seed = int(hashlib.blake2b(normalized.encode("utf-8"), digest_size=8).hexdigest(), 16)
            rng = random.Random(seed)
            out = v + [rng.random() for _ in range(dim - len(v))]
            with _CACHE_LOCK:
                _store_cached_vector(normalized, dim, out)
            return out
        except Exception:
            # fall through to hash embedding
            pass

    data = normalized.encode("utf-8")
    seed = int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")
    rng = random.Random(seed)
    out = [rng.random() for _ in range(dim)]
    with _CACHE_LOCK:
        _store_cached_vector(normalized, dim, out)
    return out
