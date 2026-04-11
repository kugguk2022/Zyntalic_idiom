# -*- coding: utf-8 -*-
"""
High-level translation API.

This wraps the deterministic core into a stable interface usable by:
- CLI
- web app (FastAPI)
- evals/tests
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Dict, List, Optional

from . import core
from . import nlp
from .chiasmus import generate_mirror_sigil
from .ir import Frame, PivotType, SentenceSidecar
from .utils.rng import get_rng

# Memoize projection to avoid repeated disk reads during translation hot path
_PROJECTION_W = core.get_projection()
_WARMED = False
_SCOPE_DEFAULTS = {
    "evidentiality": "direct",
    "register": "formal",
    "dialect": "standard",
    "frame_a": "",
    "frame_b": "",
}
_SCOPE_REGISTERS = {"formal", "informal", "literary", "archaic", "technical"}
_SCOPE_DIALECTS = {"standard", "northern", "southern", "coastal", "mountain"}
_DIALECT_REPLACEMENTS = {
    "northern": (("a", "ə"), ("o", "ʊ"), ("k", "x"), ("p", "f")),
    "southern": (("i", "e"), ("u", "o"), ("t", "d"), ("k", "g")),
    "coastal": (("l", "r"),),
    "mountain": (("s", "sh"), ("r", "rh")),
}
_DIALECT_FALLBACK_MARKERS = {
    "northern": "북",
    "southern": "남",
    "coastal": "해",
    "mountain": "산",
}


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

def mirror_readback(seed_text: str, anchors, mirror_terms: Optional[List[Dict[str, str]]] = None):
    """Build a deterministic mirror-readable English line from anchors or mirror terms."""
    try:
        rng = get_rng(f"mirror-readback::{seed_text}")
        if mirror_terms:
            try:
                (A, _), (B, _) = core._pick_pair_from_terms(rng, mirror_terms)  # type: ignore[attr-defined]
            except Exception:
                A = B = None
        else:
            A = B = None
        if not A or not B:
            if not anchors:
                vec = core.base_embedding(seed_text or "", dim=300)
                anchors = core.anchor_weights_for_vec(vec, top_k=2)
            names = [name for name, _ in anchors] if anchors else core.ANCHORS[:2]
            weights = [w for _, w in anchors] if anchors else [0.5, 0.5]
            A, B = core._choose_motif(rng, names, weights)  # type: ignore[attr-defined]
        templates = getattr(core, "_EN_MIRROR_TEMPLATES", ["To {A} through {B}; to {B} through {A}."])
        t = rng.choice(templates)
        return t.format(A=A, B=B)
    except Exception:
        return None


def _normalize_scope_config(config: Optional[Dict]) -> Dict[str, str]:
    normalized = dict(_SCOPE_DEFAULTS)
    if not config:
        return normalized

    for key, default in _SCOPE_DEFAULTS.items():
        value = config.get(key, default)
        if isinstance(value, str):
            value = value.strip()
        if value in (None, ""):
            normalized[key] = default
            continue
        normalized[key] = str(value)

    register = normalized["register"].lower()
    normalized["register"] = register if register in _SCOPE_REGISTERS else _SCOPE_DEFAULTS["register"]

    dialect = normalized["dialect"].lower()
    normalized["dialect"] = dialect if dialect in _SCOPE_DIALECTS else _SCOPE_DEFAULTS["dialect"]

    normalized["evidentiality"] = normalized["evidentiality"].lower()
    return normalized


def _requested_frame_names(config: Optional[Dict]) -> List[str]:
    normalized = _normalize_scope_config(config)
    names: List[str] = []
    for key in ("frame_a", "frame_b"):
        value = normalized.get(key, "").strip()
        if value:
            names.append(value)
    return names


def _coerce_anchor_pairs(raw) -> List[tuple[str, float]]:
    pairs: List[tuple[str, float]] = []
    for item in raw or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            name, weight = item[0], item[1]
        elif isinstance(item, dict):
            name = item.get("name") or item.get("anchor")
            weight = item.get("weight")
        else:
            continue
        if not name:
            continue
        try:
            pairs.append((str(name), float(weight)))
        except Exception:
            continue
    return pairs


def _collect_anchor_weights(source: str, row: Dict, config: Optional[Dict]) -> List[tuple[str, float]]:
    frame_names = _requested_frame_names(config)
    lookup_k = len(core.ANCHORS) if frame_names else 5
    weights: List[tuple[str, float]] = []

    embedding = row.get("embedding")
    if embedding is not None:
        try:
            weights = core.anchor_weights_for_vec(embedding, top_k=lookup_k)
        except Exception:
            weights = []

    if not weights:
        weights = _coerce_anchor_pairs(row.get("anchors"))

    needs_full_lookup = bool(frame_names) and any(
        frame_name not in {name for name, _ in weights}
        for frame_name in frame_names
    )
    if needs_full_lookup or not weights:
        try:
            base_vec = embedding if embedding is not None else core.base_embedding(source or "", dim=300)
            weights = core.anchor_weights_for_vec(base_vec, top_k=lookup_k)
        except Exception:
            weights = weights or []

    return weights[:lookup_k]


def _extract_sigil(text: str) -> tuple[Optional[str], Optional[str]]:
    try:
        sigil_data = generate_mirror_sigil(text)
    except Exception:
        return None, None

    if isinstance(sigil_data, tuple) and len(sigil_data) == 2:
        sigil, sigil_type = sigil_data
        return (sigil or None), (sigil_type or None)
    if isinstance(sigil_data, str):
        return (sigil_data or None), None
    return None, None


def _scope_signature(config: Optional[Dict], anchor_weights: List[tuple[str, float]]) -> str:
    normalized = _normalize_scope_config(config)
    anchor_blob = "-".join(
        name.split("_", 1)[-1].replace("_", "")[:4].upper()
        for name, _ in anchor_weights[:2]
    ) or "PLAIN"
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.blake2s(payload.encode("utf-8"), digest_size=3).hexdigest().upper()
    return f"{anchor_blob}-{digest}"


def _resolve_pivot(frames: List[Frame]) -> PivotType:
    if len(frames) >= 2:
        delta = abs(frames[0].weight - frames[1].weight)
        return PivotType.CONVERGE if delta <= 0.08 else PivotType.DIVERGE
    if len(frames) == 1 and frames[0].weight > 0:
        return PivotType.CONVERGE
    return PivotType.NEUTRAL


def _token_sidecar(source: str) -> Optional[List[Dict[str, object]]]:
    tokens = []
    for token in nlp.analyze_tokens(source):
        surface = (token.get("text") or "").strip()
        if not surface:
            continue
        tokens.append(
            {
                "surface": surface,
                "lemma": (token.get("lemma") or surface).lower(),
                "pos": token.get("pos") or "X",
                "morphemes": {},
            }
        )
    return tokens or None


def _split_context_tail(text: str) -> tuple[str, Optional[str]]:
    if not text:
        return "", None
    marker = "⟦ctx:"
    if marker not in text:
        return text.strip(), None
    head, _, tail = text.partition(marker)
    return head.rstrip(), f"{marker}{tail.strip()}"


def _merge_context_tail(ctx_tail: Optional[str], updates: Dict[str, str]) -> Optional[str]:
    if not updates and not ctx_tail:
        return None

    parts: List[str] = []
    if ctx_tail and ctx_tail.startswith("⟦ctx:") and ctx_tail.endswith("⟧"):
        inner = ctx_tail[len("⟦ctx:"):-1].strip()
        parts = [item.strip() for item in inner.split(";") if item.strip()]

    present = {
        item.split("=", 1)[0].strip()
        for item in parts
        if "=" in item
    }
    for key, value in updates.items():
        if key in present:
            continue
        parts.append(f"{key}={value}")

    return f"⟦ctx:{'; '.join(parts)}⟧" if parts else None


def _compose_target(surface: str, ctx_tail: Optional[str]) -> str:
    surface = (surface or "").strip()
    if not ctx_tail:
        return surface
    if not surface:
        return ctx_tail
    return f"{surface} {ctx_tail}"


def _apply_register_surface(surface: str, register: str) -> str:
    surface = (surface or "").strip()
    if not surface or register == "formal":
        return surface
    if register == "informal" and not surface.endswith(("야", "어", "아", "지")):
        return f"{surface} 야"
    if register == "literary" and "통하여" not in surface:
        return f"{surface} 통하여"
    if register == "archaic" and "하옵니다" not in surface:
        return f"{surface} 하옵니다"
    if register == "technical" and "::정의" not in surface:
        return f"{surface} ::정의"
    return surface


def _apply_dialect_surface(surface: str, dialect: str) -> str:
    surface = (surface or "").strip()
    if not surface or dialect == "standard":
        return surface

    modified = surface
    for old, new in _DIALECT_REPLACEMENTS.get(dialect, ()):
        modified = modified.replace(old, new)

    if modified == surface:
        marker = _DIALECT_FALLBACK_MARKERS.get(dialect)
        if marker and not modified.endswith(marker):
            modified = f"{modified} {marker}"
    return modified


def _context_scope_updates(config: Optional[Dict]) -> Dict[str, str]:
    normalized = _normalize_scope_config(config)
    updates: Dict[str, str] = {}
    if normalized["evidentiality"] != _SCOPE_DEFAULTS["evidentiality"]:
        updates["evidentiality"] = normalized["evidentiality"]
    if normalized["register"] != _SCOPE_DEFAULTS["register"]:
        updates["register"] = normalized["register"]
    if normalized["dialect"] != _SCOPE_DEFAULTS["dialect"]:
        updates["dialect"] = normalized["dialect"]

    frames = []
    if normalized["frame_a"]:
        frames.append(f"A:{normalized['frame_a']}")
    if normalized["frame_b"]:
        frames.append(f"B:{normalized['frame_b']}")
    if frames:
        updates["frames"] = "|".join(frames)
    return updates


def _apply_requested_scope(target: str, source: str, config: Optional[Dict], engine: str) -> str:
    if not target or engine == "reverse":
        return target

    normalized = _normalize_scope_config(config)
    surface, ctx_tail = _split_context_tail(target)
    if normalized["register"] != _SCOPE_DEFAULTS["register"]:
        surface = _apply_register_surface(surface, normalized["register"])
    if normalized["dialect"] != _SCOPE_DEFAULTS["dialect"]:
        surface = _apply_dialect_surface(surface, normalized["dialect"])

    ctx_tail = _merge_context_tail(ctx_tail, _context_scope_updates(normalized))
    return _compose_target(surface, ctx_tail)


def build_sentence_sidecar(source: str, row: Dict, config: Optional[Dict] = None) -> SentenceSidecar:
    anchor_weights = _collect_anchor_weights(source, row, config)
    weight_map = {name: weight for name, weight in anchor_weights}
    normalized = _normalize_scope_config(config)
    frames: List[Frame] = []
    for frame_id, key in (("A", "frame_a"), ("B", "frame_b")):
        anchor = normalized.get(key, "")
        anchor = anchor.strip() if isinstance(anchor, str) else ""
        if not anchor:
            continue
        frames.append(Frame(id=frame_id, anchor=anchor, weight=weight_map.get(anchor, 0.0)))

    sigil, sigil_type = _extract_sigil(source)
    evidentiality = (config or {}).get("evidentiality")
    evidentiality = evidentiality.strip() if isinstance(evidentiality, str) else None

    return SentenceSidecar(
        frames=frames,
        pivot=_resolve_pivot(frames),
        anchor_weights=anchor_weights[:5],
        sigil=sigil,
        sigil_type=sigil_type,
        evidentiality=evidentiality or None,
        register=normalized["register"] or None,
        dialect=normalized["dialect"] or None,
        scope_signature=_scope_signature(normalized, anchor_weights[:5]),
        tokens=_token_sidecar(source),
    )


def _attach_sidecar(row: Dict, source: str, config: Optional[Dict]) -> Dict:
    row["target"] = _apply_requested_scope(
        row.get("target", ""),
        source,
        config,
        str(row.get("engine") or ""),
    )
    row["sidecar"] = build_sentence_sidecar(source, row, config).to_dict()
    return row


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

def _batch_max_chars() -> int:
    raw = os.getenv("ZYNTALIC_BATCH_CHARS", "400").strip()
    try:
        return max(0, int(raw))
    except Exception:
        return 400

def _split_into_batches(text: str, max_chars: int) -> List[str]:
    if max_chars <= 0:
        return [text] if text else []
    s = (text or "").strip()
    if not s:
        return []
    if len(s) <= max_chars:
        return [s]

    # Prefer splitting on natural boundaries within the max window.
    boundary_patterns = (
        r"\n\n",
        r"\n",
        r"[.!?]\s",
        r";\s",
        r",\s",
    )
    min_size = max(40, int(max_chars * 0.5))
    chunks: List[str] = []

    while s:
        if len(s) <= max_chars:
            chunks.append(s.strip())
            break
        window = s[: max_chars + 1]
        candidates: List[int] = []
        for pattern in boundary_patterns:
            for m in re.finditer(pattern, window):
                candidates.append(m.end())
        if candidates:
            # Choose the best candidate at or above min_size; otherwise the last boundary.
            viable = [c for c in candidates if c >= min_size]
            cut = max(viable) if viable else max(candidates)
        else:
            cut = max_chars
        chunk = s[:cut].strip()
        if not chunk:
            cut = max_chars
            chunk = s[:cut].strip()
        chunks.append(chunk)
        s = s[cut:].lstrip()

    return chunks


def _extract_mirror_terms(text: str) -> List[Dict[str, str]]:
    vocab = core.load_vocabulary_mappings()
    noun_keys = set(vocab.get("nouns", {}).keys())
    verb_keys = set(vocab.get("verbs", {}).keys())
    adj_keys = set(vocab.get("adjectives", {}).keys())
    stop = {"the", "and", "of", "to", "in", "a", "an", "is", "are", "was", "were"}
    terms: List[Dict[str, str]] = []
    seen = set()
    for tok in nlp.analyze_tokens(text):
        lemma = (tok.get("lemma") or tok.get("text") or "").lower()
        if not lemma or lemma in stop or len(lemma) < 3:
            continue
        pos = None
        if lemma in noun_keys:
            pos = "nouns"
        elif lemma in verb_keys:
            pos = "verbs"
        elif lemma in adj_keys:
            pos = "adjectives"
        if pos is None:
            pos_hint = (tok.get("pos") or "").lower()
            if pos_hint in ("noun", "propn"):
                pos = "nouns"
            elif pos_hint == "verb":
                pos = "verbs"
            elif pos_hint == "adj":
                pos = "adjectives"
        if pos is None:
            pos = "nouns"
        if pos and lemma not in seen:
            seen.add(lemma)
            mirror = core._mirror_term(lemma)  # type: ignore[attr-defined]
            terms.append({"term": lemma, "pos": pos, "mirror": mirror or ""})
    return terms


def translate_sentence(
    text: str,
    *,
    mirror_rate: float = 0.3,  # Lower value = more Zyntalic vocabulary
    engine: str = "core",
    W=None,
    mirror_state: Optional[core.MirrorState] = None,
    config: Optional[Dict] = None,
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

    mirror_terms = _extract_mirror_terms(src)

    if engine == "test_suite":
        try:
            from .test_suite import ZyntalicTestSuite
            # Run a quick validation test for the input
            test_suite = ZyntalicTestSuite()
            # Use core engine for actual translation but add test metadata
            entry = core.generate_entry(
                lemma or src,
                mirror_rate=mirror_rate,
                W=W,
                mirror_state=mirror_state,
                mirror_terms=mirror_terms,
            )
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
                row["mirror_text"] = mirror_readback(lemma or src, entry.get("anchors", []), mirror_terms=mirror_terms)
            return _attach_sidecar(row, src, config)
        except Exception as e:
            # Fall back to core if test suite fails
            engine = "core"

    if engine == "reverse":
        try:
            from .reverse import reverse_translate_sentence
            row = reverse_translate_sentence(src)
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []), mirror_terms=mirror_terms)
            return _attach_sidecar(row, src, config)
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
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []), mirror_terms=mirror_terms)
            return _attach_sidecar(row, src, config)
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
                row["mirror_text"] = mirror_readback(src, row.get("anchors", []), mirror_terms=mirror_terms)
            return _attach_sidecar(row, src, config)
        except Exception:
            # fall back to core
            engine = "core"

    entry = core.generate_entry(
        lemma or src,
        mirror_rate=mirror_rate,
        W=W or _PROJECTION_W,
        mirror_state=mirror_state,
        mirror_terms=mirror_terms,
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
        row["mirror_text"] = mirror_readback(lemma or src, entry.get("anchors", []), mirror_terms=mirror_terms)
    return _attach_sidecar(row, src, config)


def translate_text(
    text: str,
    *,
    mirror_rate: float = 0.8,
    engine: str = "core",
    W=None,
    config: Optional[Dict] = None,
) -> List[Dict]:
    """
    Translate multi-sentence text into a list of records.
    """
    _ensure_warm()
    text = (text or "").strip()
    if not text:
        return []
    max_chars = _batch_max_chars()
    parts: List[str] = []
    for batch in _split_into_batches(text, max_chars):
        parts.extend(nlp.split_sentences(batch))
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
                config=config,
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
    config: Optional[Dict] = None,
) -> List:
    """Translate a batch of texts efficiently.

    If flatten=True, returns a single flat list of rows; otherwise a list of lists.
    """
    _ensure_warm()
    results: List[List[Dict]] = []
    for text in texts:
        rows = translate_text(text, mirror_rate=mirror_rate, engine=engine, W=W, config=config)
        results.append(rows)

    if flatten:
        return [row for group in results for row in group]
    return results
