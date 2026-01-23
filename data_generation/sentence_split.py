#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Split cleaned text files into sentences and write JSONL.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from zyntalic import nlp

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[A-Za-z][A-Za-z'\-]+")


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.txt"):
        if path.is_file():
            yield path


def is_sentence_ok(text: str, min_len: int, max_len: int) -> bool:
    if len(text) < min_len or len(text) > max_len:
        return False
    words = _WORD.findall(text)
    if len(words) < 3:
        return False
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_dir", default="data_generation/clean")
    p.add_argument("--out", dest="out_file", default="data_generation/sentences/sentences.jsonl")
    p.add_argument("--min-len", type=int, default=20)
    p.add_argument("--max-len", type=int, default=400)
    args = p.parse_args()

    in_dir = Path(args.in_dir)
    out_path = Path(args.out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        for path in iter_files(in_dir):
            text = path.read_text(encoding="utf-8", errors="ignore")
            text = text.replace("\n", " ")
            sentences = nlp.split_sentences(text) or _SENT_SPLIT.split(text)
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                if not is_sentence_ok(sentence, args.min_len, args.max_len):
                    continue
                rec = {
                    "source_id": path.stem,
                    "sentence": sentence,
                    "source_path": str(path),
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
