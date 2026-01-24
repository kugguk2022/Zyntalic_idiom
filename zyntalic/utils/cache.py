# -*- coding: utf-8 -*-
"""Simple translation cache to keep source→target pairs stable.

Stores entries in JSON at data/cache/translations.json. Each entry includes:
- source (str)
- target (str)
- engine (str)
- mirror_rate (float)
- anchors (list)
- embedding (list[float])
- mirror_text (str)
- created_at (iso string)

Cache key is deterministic (engine + mirror_rate + source).
"""

from __future__ import annotations

import json
import os
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from zyntalic.embeddings import embed_text

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CACHE_DIR = os.path.join(ROOT_DIR, "data", "cache")
CACHE_PATH = os.path.join(CACHE_DIR, "translations.json")

_cache: Dict[str, Dict[str, Any]] = {}
_initialized = False


def _ensure_dirs() -> None:
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)


def _key(source: str, engine: str, mirror_rate: float) -> str:
    # Normalize source for stable key
    normalized = (source or "").strip()
    payload = f"{engine}|{mirror_rate:.4f}|{normalized}"
    digest = hashlib.blake2s(payload.encode("utf-8"), digest_size=12).hexdigest()
    return digest


def init_cache() -> None:
    """Load cache from disk once."""
    global _initialized, _cache
    if _initialized:
        return
    _ensure_dirs()
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _cache = data
        except Exception:
            _cache = {}
    _initialized = True


def save_cache() -> None:
    _ensure_dirs()
    tmp_path = CACHE_PATH + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(_cache, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, CACHE_PATH)
    except Exception:
        # Best-effort; ignore write errors
        pass


def get_cached_translation(source: str, engine: str, mirror_rate: float) -> Optional[Dict[str, Any]]:
    init_cache()
    k = _key(source, engine, mirror_rate)
    entry = _cache.get(k)
    if not entry:
        return None
    # Return a shallow copy to avoid mutation outside
    return dict(entry)


def put_cached_translation(
    source: str,
    target: str,
    engine: str,
    mirror_rate: float,
    anchors: Optional[List] = None,
    embedding: Optional[List[float]] = None,
    mirror_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Store translation and return the stored entry."""
    init_cache()
    if embedding is None:
        embedding = embed_text(target or "", dim=300)
    entry = {
        "source": source or "",
        "target": target or "",
        "engine": engine,
        "mirror_rate": float(mirror_rate),
        "anchors": anchors or [],
        "embedding": embedding,
        "mirror_text": mirror_text or "",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    _cache[_key(source, engine, mirror_rate)] = entry
    save_cache()
    return dict(entry)


def cache_size() -> int:
    init_cache()
    return len(_cache)
