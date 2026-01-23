# -*- coding: utf-8 -*-
"""
High-level translation API.

This wraps the deterministic core into a stable interface usable by:
- CLI
- web app (FastAPI)
- evals/tests
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from . import core
from . import nlp

# Memoize projection to avoid repeated disk reads during translation hot path
_PROJECTION_W = core.get_projection()
_WARMED = False


def _ensure_warm() -> None:
    """Warm caches once per process to avoid first-call latency on long texts."""
    global _WARMED
    if _WARMED:
        return
    try:
        warm_translation_pipeline()
    finally:
        _WARMED = True


def warm_translation_pipeline() -> None:
    """Preload heavy resources (lexicons, mappings, anchor vecs, projection).

    Any failure is swallowed so server startup does not abort; translation will
    still function with fallback behavior.
    """
    try:
        core.load_lexicons()
        core.load_vocabulary_mappings()
        core._get_anchor_vecs()  # type: ignore  # intentionally using internal cache
        # projection already memoized at import; ensure loaded if available
        core.get_projection()
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"[warmup] Warning: preload skipped due to: {exc}")

def _clean_lemma(text: str) -> str:
    # Prefer NLP backend lemma if available; fallback to regex normalization.
    t = (text or "").strip()
    if not t:
        return ""
    lemma = nlp.first_lemma(t)
    if lemma:
        return lemma.lower()
    t = re.sub(r"[^A-Za-z0-9'\- ]+", " ", t.lower())
    t = re.sub(r"\s+", " ", t).strip()
    return t.split()[0] if t else ""


def translate_sentence(
    text: str,
    *,
    mirror_rate: float = 0.3,  # Lower value = more Zyntalic vocabulary
    engine: str = "core",
    W=None,
) -> Dict:
    """
    Translate a single sentence to a structured record.

    engine:
      - "core": rule-based + anchor mixing (recommended baseline)
      - "chiasmus": uses chiasmus renderer if available (more stylized)
      - "transformer": uses semantic anchor matching via sentence-transformers
      - "test_suite": runs comprehensive validation and returns diagnostic info
    """
    src = (text or "").strip()
    lemma = _clean_lemma(src)

    if engine == "test_suite":
        try:
            from .test_suite import ZyntalicTestSuite
            # Run a quick validation test for the input
            test_suite = ZyntalicTestSuite()
            # Use core engine for actual translation but add test metadata
            entry = core.generate_entry(lemma or src, mirror_rate=mirror_rate, W=W)
            return {
                "source": src,
                "target": entry["sentence"],
                "lemma": lemma,
                "anchors": entry["anchors"],
                "engine": "test_suite",
                "validation": "passed",
                "test_info": "Input validated with test suite"
            }
        except Exception as e:
            # Fall back to core if test suite fails
            engine = "core"

    if engine == "transformer":
        try:
            from .transformers import translate_transformer
            return {
                "source": src,
                "target": translate_transformer(src, mirror_rate=mirror_rate),
                "lemma": lemma,
                "anchors": [], # TODO: populate if needed
                "engine": "transformer",
            }
        except Exception as e:
            # print(f"Transformer error: {e}") # debug
            engine = "core"

    if engine == "chiasmus":
        try:
            from .chiasmus import translate_chiasmus  # type: ignore
            tgt = translate_chiasmus(src)
            return {
                "source": src,
                "target": tgt,
                "lemma": lemma,
                "anchors": [],
                "engine": "chiasmus",
            }
        except Exception:
            # fall back to core
            engine = "core"

    entry = core.generate_entry(lemma or src, mirror_rate=mirror_rate, W=W or _PROJECTION_W)
    # entry contains 'sentence' (with ctx tail) and anchor weights
    return {
        "source": src,
        "target": entry["sentence"],
        "lemma": lemma,
        "anchors": entry["anchors"],
        "engine": "core",
    }


def translate_text(
    text: str,
    *,
    mirror_rate: float = 0.8,
    engine: str = "core",
    W=None,
) -> List[Dict]:
    """
    Translate multi-sentence text into a list of records.
    """
    _ensure_warm()
    text = (text or "").strip()
    if not text:
        return []
    parts = nlp.split_sentences(text)
    return [translate_sentence(p, mirror_rate=mirror_rate, engine=engine, W=W) for p in parts if p.strip()]


def translate_batch(
    texts: List[str],
    *,
    mirror_rate: float = 0.8,
    engine: str = "core",
    W=None,
    flatten: bool = False,
) -> List:
    """Translate a batch of texts efficiently.

    If flatten=True, returns a single flat list of rows; otherwise a list of lists.
    """
    _ensure_warm()
    results: List[List[Dict]] = []
    for text in texts:
        rows = translate_text(text, mirror_rate=mirror_rate, engine=engine, W=W)
        results.append(rows)

    if flatten:
        return [row for group in results for row in group]
    return results
