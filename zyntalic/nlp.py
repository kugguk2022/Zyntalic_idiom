"""
Optional NLP backend utilities (sentence splitting, tokenization, lemmatization).

This module prefers spaCy when available, but always falls back to a lightweight
regex implementation to keep the core deterministic and dependency-light.
"""

from __future__ import annotations

import logging
import os
import re

logger = logging.getLogger("zyntalic.nlp")

_SENT_SPLIT_FALLBACK = re.compile(r"(?<=[.!?])\s+")
_WORD_FALLBACK = re.compile(r"[A-Za-z][A-Za-z'\-]+")

_NLP = None
_BACKEND = None  # "spacy" or "fallback"


def _backend_setting() -> str:
    return os.getenv("ZYNTALIC_NLP", "auto").strip().lower()


def _load_spacy():
    try:
        import spacy  # type: ignore
    except Exception:
        return None

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return None


def _ensure_backend() -> None:
    global _NLP, _BACKEND
    if _BACKEND is not None:
        return

    setting = _backend_setting()
    if setting in ("none", "off", "false", "0"):
        _BACKEND = "fallback"
        _NLP = None
        return

    nlp = _load_spacy()
    if nlp is None:
        if setting == "spacy":
            logger.warning("spaCy requested but not available; falling back to regex.")
        _BACKEND = "fallback"
        _NLP = None
        return

    _BACKEND = "spacy"
    _NLP = nlp


def backend_name() -> str:
    _ensure_backend()
    return _BACKEND or "fallback"


def split_sentences(text: str) -> list[str]:
    _ensure_backend()
    if not text:
        return []

    if _BACKEND == "spacy" and _NLP is not None:
        doc = _NLP(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]

    return [s.strip() for s in _SENT_SPLIT_FALLBACK.split(text) if s.strip()]


def analyze_tokens(text: str) -> list[dict[str, str]]:
    _ensure_backend()
    if not text:
        return []

    if _BACKEND == "spacy" and _NLP is not None:
        doc = _NLP(text)
        out = []
        for token in doc:
            if token.is_space:
                continue
            out.append({
                "text": token.text,
                "lemma": token.lemma_ or token.text,
                "pos": token.pos_ or "X",
            })
        return out

    # fallback: whitespace tokenization + simple lemma
    tokens = _WORD_FALLBACK.findall(text)
    return [{"text": t, "lemma": t.lower(), "pos": "X"} for t in tokens]


def first_lemma(text: str) -> str:
    tokens = analyze_tokens(text)
    if not tokens:
        return ""
    return tokens[0].get("lemma") or tokens[0].get("text") or ""
