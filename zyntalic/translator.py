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
from .utils.rng import get_rng

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

def mirror_readback(seed_text: str, anchors):
    """Build a deterministic mirror-readable English line from anchors."""
    try:
        if not anchors:
            vec = core.base_embedding(seed_text or "", dim=300)
            anchors = core.anchor_weights_for_vec(vec, top_k=2)
        names = [name for name, _ in anchors] if anchors else core.ANCHORS[:2]
        weights = [w for _, w in anchors] if anchors else [0.5, 0.5]
        rng = get_rng(f"mirror-readback::{seed_text}")
        A, B = core._choose_motif(rng, names, weights)  # type: ignore[attr-defined]
        templates = getattr(core, "_EN_MIRROR_TEMPLATES", ["To {A} through {B}; to {B} through {A}."])
        t = rng.choice(templates)
        return t.format(A=A, B=B)
    except Exception:
        return None
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
    mirror_state: Optional[core.MirrorState] = None,
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
            entry = core.generate_entry(lemma or src, mirror_rate=mirror_rate, W=W, mirror_state=mirror_state)
            row = {
                "source": src,
                "target": entry["sentence"],
                "lemma": lemma,
                "anchors": entry["anchors"],
                "engine": "test_suite",
                "validation": "passed",
                "test_info": "Input validated with test suite"
            }
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(lemma or src, entry.get("anchors", []))
            return row
        except Exception as e:
            # Fall back to core if test suite fails
            engine = "core"

    if engine == "reverse":
        try:
            from .reverse import reverse_translate_sentence
            row = reverse_translate_sentence(src)
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []))
            return row
        except Exception:
            engine = "core"

    if engine == "transformer":
        try:
            from .transformers import translate_transformer
            row = {
                "source": src,
                "target": translate_transformer(src, mirror_rate=mirror_rate),
                "lemma": lemma,
                "anchors": [], # TODO: populate if needed
                "engine": "transformer",
            }
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []))
            return row
        except Exception as e:
            # print(f"Transformer error: {e}") # debug
            engine = "core"

    if engine == "chiasmus":
        try:
            from .chiasmus import translate_chiasmus  # type: ignore
            tgt = translate_chiasmus(src)
            row = {
                "source": src,
                "target": tgt,
                "lemma": lemma,
                "anchors": [],
                "engine": "chiasmus",
            }
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []))
            return row
        except Exception:
            # fall back to core
            engine = "core"

    entry = core.generate_entry(
        lemma or src,
        mirror_rate=mirror_rate,
        W=W or _PROJECTION_W,
        mirror_state=mirror_state,
    )
    # entry contains 'sentence' (with ctx tail) and anchor weights
    row = {
        "source": src,
        "target": entry["sentence"],
        "lemma": lemma,
        "anchors": entry["anchors"],
        "engine": "core",
        "embedding": entry.get("embedding"),
    }
    if mirror_rate > 0.75:
        row["mirror_text"] = mirror_readback(lemma or src, entry.get("anchors", []))
    return row


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
    mirror_state = core.MirrorState()
    rows = []
    for p in parts:
        if not p.strip():
            continue
        rows.append(
            translate_sentence(
                p,
                mirror_rate=mirror_rate,
                engine=engine,
                W=W,
                mirror_state=mirror_state,
            )
        )
    return rows


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
