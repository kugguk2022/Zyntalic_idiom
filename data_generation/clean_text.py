#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalize and clean raw text files into a consistent corpus.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

_START_RE = re.compile(r"\*\*\*\s*START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)
_END_RE = re.compile(r"\*\*\*\s*END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK", re.IGNORECASE)


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.txt"):
        if path.is_file():
            yield path


def strip_gutenberg_boilerplate(text: str) -> str:
    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and _START_RE.search(line):
            start_idx = i + 1
        if end_idx is None and _END_RE.search(line):
            end_idx = i
            break
    if start_idx is not None and end_idx is not None and start_idx < end_idx:
        return "\n".join(lines[start_idx:end_idx]).strip()
    return text


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\t+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_dir", default="data_generation/raw_text")
    p.add_argument("--out", dest="out_dir", default="data_generation/clean")
    p.add_argument("--gutenberg", action="store_true")
    p.add_argument("--min-chars", type=int, default=500)
    args = p.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in iter_files(in_dir):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if args.gutenberg:
            text = strip_gutenberg_boilerplate(text)
        text = normalize(text)
        if len(text) < args.min_chars:
            continue
        out_path = out_dir / path.name
        out_path.write_text(text, encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
