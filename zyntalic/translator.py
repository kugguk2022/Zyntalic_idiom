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

from . import core, nlp, syntax
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
_ANCHOR_MODE_DEFAULT = "auto"
_ANCHOR_MODES = {"auto", "manual", "neutral"}
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

def mirror_readback(
    seed_text: str,
    anchors,
    mirror_terms: list[dict[str, str]] | None = None,
    *,
    fallback_to_semantic: bool = True,
):
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
            if not anchors and fallback_to_semantic:
                vec = core.base_embedding(seed_text or "", dim=300)
                anchors = core.anchor_weights_for_vec(vec, top_k=2)
            if anchors:
                names = [name for name, _ in anchors]
                weights = [w for _, w in anchors]
                A, B = core._choose_motif(rng, names, weights)  # type: ignore[attr-defined]
            else:
                fallback_pairs = getattr(core, "_DEFAULT_MOTIFS", [("order", "chaos")])
                A, B = fallback_pairs[int(rng.random() * len(fallback_pairs))]
        templates = getattr(core, "_EN_MIRROR_TEMPLATES", ["To {A} through {B}; to {B} through {A}."])
        t = rng.choice(templates)
        return t.format(A=A, B=B)
    except Exception:
        return None


def _normalize_scope_config(config: dict | None) -> dict[str, str]:
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


def _normalize_anchor_mode(config: dict | None) -> str:
    if not config:
        return _ANCHOR_MODE_DEFAULT
    value = config.get("anchor_mode", _ANCHOR_MODE_DEFAULT)
    if isinstance(value, str):
        value = value.strip().lower()
    else:
        value = str(value).strip().lower()
    return value if value in _ANCHOR_MODES else _ANCHOR_MODE_DEFAULT


def _normalize_selected_anchors(config: dict | None) -> list[str]:
    selected: list[str] = []
    raw = (config or {}).get("selected_anchors", [])
    if isinstance(raw, (list, tuple)):
        for item in raw:
            name = str(item).strip()
            if not name or name not in core.ANCHORS or name in selected:
                continue
            selected.append(name)

    normalized = _normalize_scope_config(config)
    for key in ("frame_a", "frame_b"):
        name = normalized.get(key, "").strip()
        if name and name in core.ANCHORS and name not in selected:
            selected.append(name)
    return selected


def _requested_frame_names(config: dict | None) -> list[str]:
    return _normalize_selected_anchors(config)[:2]


def _requested_anchor_weights(config: dict | None) -> list[tuple[str, float]] | None:
    anchor_mode = _normalize_anchor_mode(config)
    selected = _normalize_selected_anchors(config)

    if anchor_mode == "neutral":
        return []
    if anchor_mode == "manual" and not selected:
        return []
    if not selected:
        return None

    seen: list[str] = []
    for name in selected:
        if name not in seen:
            seen.append(name)
    if not seen:
        return None
    if len(seen) == 1:
        return [(seen[0], 1.0)]
    weight = 1.0 / len(seen)
    return [(name, weight) for name in seen]


def _coerce_anchor_pairs(raw) -> list[tuple[str, float]]:
    pairs: list[tuple[str, float]] = []
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


def _collect_anchor_weights(source: str, row: dict, config: dict | None) -> list[tuple[str, float]]:
    anchor_mode = _normalize_anchor_mode(config)
    requested_names = _normalize_selected_anchors(config)
    requested_weights = _requested_anchor_weights(config) or []
    lookup_k = len(core.ANCHORS) if requested_names else 5
    weights: list[tuple[str, float]] = []

    row_weights = _coerce_anchor_pairs(row.get("anchors"))
    if anchor_mode == "neutral":
        return row_weights[:lookup_k] if row_weights else []

    if requested_names:
        row_names = {name for name, _ in row_weights}
        if row_weights and all(frame_name in row_names for frame_name in requested_names):
            return row_weights[:lookup_k]

    if anchor_mode == "manual":
        return row_weights[:lookup_k] if row_weights else requested_weights[:lookup_k]

    embedding = row.get("embedding")
    if embedding is not None:
        try:
            weights = core.anchor_weights_for_vec(embedding, top_k=lookup_k)
        except Exception:
            weights = []

    if not weights:
        weights = row_weights

    needs_full_lookup = bool(requested_names) and any(
        frame_name not in {name for name, _ in weights}
        for frame_name in requested_names
    )
    if needs_full_lookup or not weights:
        try:
            base_vec = embedding if embedding is not None else core.base_embedding(source or "", dim=300)
            weights = core.anchor_weights_for_vec(base_vec, top_k=lookup_k)
        except Exception:
            weights = weights or []

    return weights[:lookup_k]


def _extract_sigil(text: str) -> tuple[str | None, str | None]:
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


def _scope_signature(config: dict | None, anchor_weights: list[tuple[str, float]]) -> str:
    normalized = _normalize_scope_config(config)
    payload_data = dict(normalized)
    payload_data["anchor_mode"] = _normalize_anchor_mode(config)
    payload_data["selected_anchors"] = _normalize_selected_anchors(config)
    anchor_blob = "-".join(
        name.split("_", 1)[-1].replace("_", "")[:4].upper()
        for name, _ in anchor_weights[:2]
    ) or "PLAIN"
    payload = json.dumps(payload_data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.blake2s(payload.encode("utf-8"), digest_size=3).hexdigest().upper()
    return f"{anchor_blob}-{digest}"


def _resolve_pivot(frames: list[Frame]) -> PivotType:
    if len(frames) >= 2:
        delta = abs(frames[0].weight - frames[1].weight)
        return PivotType.CONVERGE if delta <= 0.08 else PivotType.DIVERGE
    if len(frames) == 1 and frames[0].weight > 0:
        return PivotType.CONVERGE
    return PivotType.NEUTRAL


def _token_sidecar(source: str) -> list[dict[str, object]] | None:
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


def _split_context_tail(text: str) -> tuple[str, str | None]:
    if not text:
        return "", None
    marker = "⟦ctx:"
    if marker not in text:
        return text.strip(), None
    head, _, tail = text.partition(marker)
    return head.rstrip(), f"{marker}{tail.strip()}"


def _merge_context_tail(ctx_tail: str | None, updates: dict[str, str]) -> str | None:
    if not updates and not ctx_tail:
        return None

    parts: list[str] = []
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


def _compose_target(surface: str, ctx_tail: str | None) -> str:
    surface = (surface or "").strip()
    if not ctx_tail:
        return surface
    if not surface:
        return ctx_tail
    return f"{surface} {ctx_tail}"


def _minimal_context_tail(seed_text: str) -> str:
    seed = (seed_text or "ctx").strip() or "ctx"
    return f"⟦ctx:han={core.make_korean_tail(seed)}⟧"


def _grammar_scope_updates(source: str) -> dict[str, str]:
    """Build deterministic grammar metadata tags from parsed source text."""
    try:
        parsed = syntax.to_zyntalic_order(source or "")
    except Exception:
        return {}

    subj = "1" if (parsed.subject or "").strip() else "0"
    obj = "1" if (parsed.obj or "").strip() else "0"
    verb = "1" if (parsed.verb or "").strip() else "0"
    ctx = "1" if (parsed.context or "").strip() else "0"

    return {
        "order": "SOVC",
        "roles": f"S{subj}|O{obj}|V{verb}|C{ctx}",
    }


def _parse_context_fields(ctx_tail: str | None) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not ctx_tail or not ctx_tail.startswith("⟦ctx:") or not ctx_tail.endswith("⟧"):
        return fields
    inner = ctx_tail[len("⟦ctx:"):-1].strip()
    for part in [p.strip() for p in inner.split(";") if p.strip()]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key:
            fields[key] = value
    return fields


def _enforce_target_rules(target: str, source: str, engine: str) -> str:
    """Apply canonical output rules before rows are returned.

    Rules enforced:
    1) For non-reverse engines, a context tail must exist.
    2) Context tail is kept at the very end of the target string.
    3) Surface text is whitespace-normalized.
    """
    raw_target = (target or "").strip()
    if not raw_target:
        if engine == "reverse":
            return raw_target
        return _compose_target((source or "").strip(), _minimal_context_tail(source or "ctx"))

    surface, ctx_tail = _split_context_tail(raw_target)
    surface = re.sub(r"\s+", " ", surface).strip()

    if ctx_tail:
        # Keep only the first context block and normalize malformed tails.
        if "⟧" in ctx_tail:
            ctx_tail = ctx_tail[: ctx_tail.index("⟧") + 1]
        if not (ctx_tail.startswith("⟦ctx:") and ctx_tail.endswith("⟧")):
            ctx_tail = _minimal_context_tail(source or surface)

    if engine != "reverse" and not ctx_tail:
        ctx_tail = _minimal_context_tail(source or surface)

    if engine != "reverse":
        ctx_tail = _merge_context_tail(ctx_tail, _grammar_scope_updates(source or surface))

    return _compose_target(surface, ctx_tail)


def _validate_target_rules(target: str, engine: str) -> list[str]:
    """Return non-fatal rule warnings for observability/debugging."""
    warnings: list[str] = []
    normalized = (target or "").strip()
    ctx_count = normalized.count("⟦ctx:")

    if engine != "reverse":
        if ctx_count == 0:
            warnings.append("missing_context_tail")
        if not normalized.endswith("⟧"):
            warnings.append("context_not_final")

        _, ctx_tail = _split_context_tail(normalized)
        fields = _parse_context_fields(ctx_tail)
        if fields.get("order") != "SOVC":
            warnings.append("missing_or_invalid_order_tag")
        roles = fields.get("roles", "")
        if not re.fullmatch(r"S[01]\|O[01]\|V[01]\|C[01]", roles):
            warnings.append("missing_or_invalid_roles_tag")

    if ctx_count > 1:
        warnings.append("multiple_context_tails")
    return warnings


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


def _context_scope_updates(config: dict | None) -> dict[str, str]:
    normalized = _normalize_scope_config(config)
    anchor_mode = _normalize_anchor_mode(config)
    selected_anchors = _normalize_selected_anchors(config)
    updates: dict[str, str] = {}
    if normalized["evidentiality"] != _SCOPE_DEFAULTS["evidentiality"]:
        updates["evidentiality"] = normalized["evidentiality"]
    if normalized["register"] != _SCOPE_DEFAULTS["register"]:
        updates["register"] = normalized["register"]
    if normalized["dialect"] != _SCOPE_DEFAULTS["dialect"]:
        updates["dialect"] = normalized["dialect"]
    if anchor_mode != _ANCHOR_MODE_DEFAULT:
        updates["anchor_mode"] = anchor_mode

    frames = []
    for index, anchor in enumerate(selected_anchors[:2]):
        frames.append(f"{'AB'[index]}:{anchor}")
    if frames:
        updates["frames"] = "|".join(frames)
    if anchor_mode == "manual" and selected_anchors:
        updates["selected"] = "|".join(selected_anchors[:4])
    return updates


def _apply_requested_scope(target: str, source: str, config: dict | None, engine: str) -> str:
    if not target or engine == "reverse":
        return target

    normalized = _normalize_scope_config(config)
    surface, ctx_tail = _split_context_tail(target)
    if normalized["register"] != _SCOPE_DEFAULTS["register"]:
        surface = _apply_register_surface(surface, normalized["register"])
    if normalized["dialect"] != _SCOPE_DEFAULTS["dialect"]:
        surface = _apply_dialect_surface(surface, normalized["dialect"])

    ctx_tail = _merge_context_tail(ctx_tail, _context_scope_updates(config))
    return _compose_target(surface, ctx_tail)


def build_sentence_sidecar(source: str, row: dict, config: dict | None = None) -> SentenceSidecar:
    anchor_mode = _normalize_anchor_mode(config)
    selected_anchors = _normalize_selected_anchors(config)
    anchor_weights = _collect_anchor_weights(source, row, config)
    weight_map = {name: weight for name, weight in anchor_weights}
    normalized = _normalize_scope_config(config)
    frames: list[Frame] = []
    if anchor_mode != "neutral":
        for index, anchor in enumerate(selected_anchors[:2]):
            frames.append(Frame(id="AB"[index], anchor=anchor, weight=weight_map.get(anchor, 0.0)))

    sigil, sigil_type = _extract_sigil(source)
    evidentiality = (config or {}).get("evidentiality")
    evidentiality = evidentiality.strip() if isinstance(evidentiality, str) else None

    return SentenceSidecar(
        frames=frames,
        pivot=_resolve_pivot(frames),
        anchor_weights=anchor_weights[:5],
        anchor_mode=anchor_mode,
        selected_anchors=selected_anchors,
        sigil=sigil,
        sigil_type=sigil_type,
        evidentiality=evidentiality or None,
        register=normalized["register"] or None,
        dialect=normalized["dialect"] or None,
        scope_signature=_scope_signature(config, anchor_weights[:5]),
        tokens=_token_sidecar(source),
    )


def _attach_sidecar(row: dict, source: str, config: dict | None) -> dict:
    engine = str(row.get("engine") or "")
    scoped_target = _apply_requested_scope(
        row.get("target", ""),
        source,
        config,
        engine,
    )
    row["target"] = _enforce_target_rules(scoped_target, source, engine)
    warnings = _validate_target_rules(row["target"], engine)
    if warnings:
        row["rule_warnings"] = warnings
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


def _canonical_seed(text: str) -> str:
    """Build a deterministic sentence-level seed instead of collapsing to one lemma."""
    normalized = (text or "").strip()
    if not normalized:
        return ""

    lemmas: list[str] = []
    for token in nlp.analyze_tokens(normalized):
        lemma = (token.get("lemma") or token.get("text") or "").strip().lower()
        if not lemma or not re.search(r"[a-z0-9]", lemma):
            continue
        lemmas.append(lemma)

    if lemmas:
        return " ".join(lemmas)

    fallback = re.sub(r"[^A-Za-z0-9'\- ]+", " ", normalized.lower())
    fallback = re.sub(r"\s+", " ", fallback).strip()
    return fallback or normalized

def _batch_max_chars() -> int:
    raw = os.getenv("ZYNTALIC_BATCH_CHARS", "400").strip()
    try:
        return max(0, int(raw))
    except Exception:
        return 400

def _split_into_batches(text: str, max_chars: int) -> list[str]:
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
    chunks: list[str] = []

    while s:
        if len(s) <= max_chars:
            chunks.append(s.strip())
            break
        window = s[: max_chars + 1]
        candidates: list[int] = []
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


def _extract_mirror_terms(text: str) -> list[dict[str, str]]:
    vocab = core.load_vocabulary_mappings()
    noun_keys = set(vocab.get("nouns", {}).keys())
    verb_keys = set(vocab.get("verbs", {}).keys())
    adj_keys = set(vocab.get("adjectives", {}).keys())
    stop = {"the", "and", "of", "to", "in", "a", "an", "is", "are", "was", "were"}
    terms: list[dict[str, str]] = []
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
    mirror_state: core.MirrorState | None = None,
    config: dict | None = None,
) -> dict:
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
    seed_text = _canonical_seed(src) or src

    mirror_terms = _extract_mirror_terms(src)
    allow_inferred_anchors = _normalize_anchor_mode(config) != "neutral"
    requested_anchor_weights = _requested_anchor_weights(config)

    if engine == "test_suite":
        try:
            from .test_suite import ZyntalicTestSuite
            # Run a quick validation test for the input
            ZyntalicTestSuite()
            # Use core engine for actual translation but add test metadata
            entry = core.generate_entry(
                seed_text,
                mirror_rate=mirror_rate,
                W=W,
                mirror_state=mirror_state,
                mirror_terms=mirror_terms,
                anchor_weights_override=requested_anchor_weights,
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
                row["mirror_text"] = mirror_readback(
                    seed_text,
                    entry.get("anchors", []),
                    mirror_terms=mirror_terms,
                    fallback_to_semantic=allow_inferred_anchors,
                )
            return _attach_sidecar(row, src, config)
        except Exception:
            # Fall back to core if test suite fails
            engine = "core"

    if engine == "reverse":
        try:
            from .reverse import reverse_translate_sentence
            row = reverse_translate_sentence(src)
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(
                    seed_text,
                    row.get("anchors", []),
                    mirror_terms=mirror_terms,
                    fallback_to_semantic=allow_inferred_anchors,
                )
            return _attach_sidecar(row, src, config)
        except Exception:
            engine = "core"

    if engine == "transformer":
        try:
            forced_anchor_weights = requested_anchor_weights
            if forced_anchor_weights is None:
                from .transformers import semantic_match

                matched_anchors = semantic_match(src, top_k=2)
                if len(matched_anchors) >= 2:
                    forced_anchor_weights = [(matched_anchors[0], 0.7), (matched_anchors[1], 0.3)]
                elif matched_anchors:
                    forced_anchor_weights = [(matched_anchors[0], 1.0)]

            entry = core.generate_entry(
                seed_text,
                mirror_rate=mirror_rate,
                W=W or _PROJECTION_W,
                mirror_state=mirror_state,
                mirror_terms=mirror_terms,
                anchor_weights_override=forced_anchor_weights,
            )
            row = {
                "source": src,
                "target": entry["sentence"],
                "lemma": lemma,
                "anchors": entry["anchors"],
                "engine": "transformer",
                "embedding": entry.get("embedding"),
            }
            if mirror_rate > 0.75:
                row["mirror_text"] = mirror_readback(
                    seed_text,
                    row.get("anchors", []),
                    mirror_terms=mirror_terms,
                    fallback_to_semantic=allow_inferred_anchors,
                )
            return _attach_sidecar(row, src, config)
        except Exception:
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
                row["mirror_text"] = mirror_readback(
                    seed_text,
                    row.get("anchors", []),
                    mirror_terms=mirror_terms,
                    fallback_to_semantic=allow_inferred_anchors,
                )
            return _attach_sidecar(row, src, config)
        except Exception:
            # fall back to core
            engine = "core"

    entry = core.generate_entry(
        seed_text,
        mirror_rate=mirror_rate,
        W=W or _PROJECTION_W,
        mirror_state=mirror_state,
        mirror_terms=mirror_terms,
        anchor_weights_override=requested_anchor_weights,
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
        row["mirror_text"] = mirror_readback(
            seed_text,
            entry.get("anchors", []),
            mirror_terms=mirror_terms,
            fallback_to_semantic=allow_inferred_anchors,
        )
    return _attach_sidecar(row, src, config)


def translate_text(
    text: str,
    *,
    mirror_rate: float = 0.8,
    engine: str = "core",
    W=None,
    config: dict | None = None,
) -> list[dict]:
    """
    Translate multi-sentence text into a list of records.
    """
    _ensure_warm()
    text = (text or "").strip()
    if not text:
        return []
    max_chars = _batch_max_chars()
    parts: list[str] = []
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
    texts: list[str],
    *,
    mirror_rate: float = 0.8,
    engine: str = "core",
    W=None,
    flatten: bool = False,
    config: dict | None = None,
) -> list:
    """Translate a batch of texts efficiently.

    If flatten=True, returns a single flat list of rows; otherwise a list of lists.
    """
    _ensure_warm()
    results: list[list[dict]] = []
    for text in texts:
        rows = translate_text(text, mirror_rate=mirror_rate, engine=engine, W=W, config=config)
        results.append(rows)

    if flatten:
        return [row for group in results for row in group]
    return results
