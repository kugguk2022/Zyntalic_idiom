"""
Reverse translation utilities (Zyntalic -> English-ish).

This is a heuristic decoder that:
- strips the context tail if present,
- maps Zyntalic tokens back to English via inverted vocab mappings,
- estimates anchors from embeddings to provide a readable context line.
"""

from __future__ import annotations

import re

from . import core

_CONTEXT_RE = re.compile(r"\s*⟦ctx:[^⟧]*⟧\s*$")
_TOKEN_RE = re.compile(r"^([^\w]*)([\w\-]+)([^\w]*)$", re.UNICODE)

_REVERSE_CACHE: dict[str, dict[str, str]] | None = None


def _strip_context_tail(text: str) -> tuple[str, str | None]:
    if not text:
        return "", None
    m = _CONTEXT_RE.search(text)
    if not m:
        return text, None
    return text[: m.start()].strip(), m.group(0)


def _looks_zyntalic(text: str) -> bool:
    # Heuristic: Zyntalic surface forms usually contain non-ASCII glyphs.
    return any(ord(ch) > 127 for ch in text)


def _build_reverse_vocab() -> dict[str, dict[str, str]]:
    vocab = core.load_vocabulary_mappings()
    reverse: dict[str, dict[str, str]] = {
        "adjectives": {},
        "nouns": {},
        "verbs": {},
        "any": {},
    }
    for pos in ("adjectives", "nouns", "verbs"):
        for en, zy in vocab.get(pos, {}).items():
            if not isinstance(zy, str):
                continue
            for key in (zy, zy.lower()):
                if key and key not in reverse[pos]:
                    reverse[pos][key] = en
                if key and key not in reverse["any"]:
                    reverse["any"][key] = en
    return reverse


def _reverse_vocab() -> dict[str, dict[str, str]]:
    global _REVERSE_CACHE
    if _REVERSE_CACHE is None:
        _REVERSE_CACHE = _build_reverse_vocab()
    return _REVERSE_CACHE


def _decode_token(token: str, pos_map: dict[str, str], any_map: dict[str, str]) -> str:
    m = _TOKEN_RE.match(token)
    if not m:
        return token
    pre, core_tok, post = m.groups()
    key = core_tok
    key_lower = core_tok.lower()
    en = pos_map.get(key) or pos_map.get(key_lower) or any_map.get(key) or any_map.get(key_lower)
    if not en:
        return token
    return f"{pre}{en}{post}"


def _decode_tokens(tokens: list[str]) -> str:
    rev = _reverse_vocab()
    if not tokens:
        return ""
    if len(tokens) == 3:
        mapped = [
            _decode_token(tokens[0], rev["adjectives"], rev["any"]),
            _decode_token(tokens[1], rev["nouns"], rev["any"]),
            _decode_token(tokens[2], rev["verbs"], rev["any"]),
        ]
        return " ".join(mapped).strip()
    return " ".join(_decode_token(t, rev["any"], rev["any"]) for t in tokens).strip()


def estimate_anchors(text: str, top_k: int = 3):
    if not text:
        return []
    vec = core.base_embedding(text, dim=300)
    return core.anchor_weights_for_vec(vec, top_k=top_k)


def format_context(anchors) -> str:
    if not anchors:
        return ""
    parts = [f"{name.replace('_', ' ')} ({w:.2f})" for name, w in anchors]
    return "Context: " + ", ".join(parts)


def reverse_translate_sentence(text: str) -> dict:
    src = (text or "").strip()
    stripped, _ctx = _strip_context_tail(src)
    if not stripped:
        return {
            "source": src,
            "target": "",
            "anchors": [],
            "engine": "reverse",
        }

    anchors = estimate_anchors(stripped or src, top_k=3)
    if _looks_zyntalic(stripped):
        tokens = stripped.split()
        decoded = _decode_tokens(tokens)
    else:
        # If it already looks English (e.g., mirrored templates), pass through.
        decoded = stripped

    context_line = format_context(anchors)
    target = decoded
    if context_line:
        target = f"{decoded}\n{context_line}"

    return {
        "source": src,
        "target": target,
        "anchors": anchors,
        "engine": "reverse",
    }
