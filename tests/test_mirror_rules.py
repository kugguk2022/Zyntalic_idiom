#!/usr/bin/env python
import importlib
import os
import re

import zyntalic.core as core
import zyntalic.translator as translator


def _reload_modules():
    importlib.reload(core)
    importlib.reload(translator)
    return core, translator


def _restore_env_and_reload(orig_val):
    if orig_val is None:
        os.environ.pop("ZYNTALIC_STRICT_VOCAB", None)
    else:
        os.environ["ZYNTALIC_STRICT_VOCAB"] = orig_val
    _reload_modules()


def test_mirror_output_no_english_templates(monkeypatch):
    orig = os.environ.get("ZYNTALIC_STRICT_VOCAB")
    try:
        monkeypatch.setenv("ZYNTALIC_STRICT_VOCAB", "1")
        _, tr = _reload_modules()

        text = "Order and chaos. Light and dark. Spirit and flesh. Time and eternity."
        rows = tr.translate_text(text, mirror_rate=1.0, engine="core")

        english_markers = [
            r"\bbetween\b",
            r"\bbegets\b",
            r"\breframes\b",
            r"\bseek\b",
            r"\bto\b",
        ]
        marker_re = re.compile("|".join(english_markers), re.IGNORECASE)

        for row in rows:
            target = row["target"].split("⟦ctx")[0].lower()
            assert not marker_re.search(target), f"English mirror template leaked: {target}"
    finally:
        _restore_env_and_reload(orig)


def test_mirror_text_included_when_high_mirror_rate(monkeypatch):
    orig = os.environ.get("ZYNTALIC_STRICT_VOCAB")
    try:
        monkeypatch.setenv("ZYNTALIC_STRICT_VOCAB", "1")
        _, tr = _reload_modules()

        row = tr.translate_text("Test mirror.", mirror_rate=0.8, engine="core")[0]
        assert row.get("mirror_text"), "mirror_text missing when mirror_rate > 0.75"
    finally:
        _restore_env_and_reload(orig)


def test_strict_vocab_tokens_from_mapping(monkeypatch):
    orig = os.environ.get("ZYNTALIC_STRICT_VOCAB")
    try:
        monkeypatch.setenv("ZYNTALIC_STRICT_VOCAB", "1")
        c, tr = _reload_modules()

        row = tr.translate_text("Simple test.", mirror_rate=0.0, engine="core")[0]
        body = row["target"].split("⟦ctx")[0].strip()
        tokens = body.split()
        assert len(tokens) >= 3, f"Unexpected token count: {tokens}"

        vocab = c.load_vocabulary_mappings()
        pool = set(vocab.get("adjectives", {}).values())
        pool |= set(vocab.get("nouns", {}).values())
        pool |= set(vocab.get("verbs", {}).values())

        for tok in tokens[:3]:
            assert tok in pool, f"Token not from vocabulary mappings: {tok}"
    finally:
        _restore_env_and_reload(orig)
