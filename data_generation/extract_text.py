#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract text from raw files into a flat text corpus directory.

Supports:
- .txt (passthrough)
- .pdf (if PyPDF2 is installed)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

try:
    import PyPDF2  # type: ignore
    HAS_PDF = True
except Exception:
    HAS_PDF = False


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def extract_pdf(path: Path) -> str:
    if not HAS_PDF:
        return ""
    text_parts = []
    with path.open("rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                continue
    return "\n".join(text_parts).strip()


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="in_dir", default="data_generation/raw")
    p.add_argument("--out", dest="out_dir", default="data_generation/raw_text")
    args = p.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in iter_files(in_dir):
        suffix = path.suffix.lower()
        out_path = out_dir / (path.stem + ".txt")

        if suffix == ".txt":
            out_path.write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
            continue

        if suffix == ".pdf":
            text = extract_pdf(path)
            if not text:
                print(f"[skip] PDF extraction failed: {path}")
                continue
            out_path.write_text(text, encoding="utf-8")
            continue

        print(f"[skip] Unsupported file type: {path}")

    if not HAS_PDF:
        print("Note: PyPDF2 not installed; PDF extraction skipped. Install with: pip install -e .[pdf]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
