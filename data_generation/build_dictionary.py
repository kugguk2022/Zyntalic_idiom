#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a dictionary from a sentence corpus by translating unique tokens.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable

try:
    import requests
except Exception:
    requests = None

_TOKEN = re.compile(r"[A-Za-z][A-Za-z'\-]+")


def iter_jsonl(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def translate_word_api(word: str, mirror_rate: float, engine: str) -> Dict:
    from zyntalic import translator
    row = translator.translate_sentence(word, mirror_rate=mirror_rate, engine=engine)
    return row


def translate_word_server(word: str, mirror_rate: float, engine: str, url: str) -> Dict:
    if requests is None:
        raise SystemExit("requests not available. Install with: pip install -e .[data]")
    payload = {"text": word, "mirror_rate": mirror_rate, "engine": engine}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("rows"):
        return {}
    return data["rows"][0]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data_generation/sentences/sentences.jsonl")
    p.add_argument("--output", default="data_generation/dictionary/zyntalic_dictionary.json")
    p.add_argument("--output-tsv", default="data_generation/dictionary/zyntalic_dictionary.tsv")
    p.add_argument("--mode", choices=["api", "server"], default="api")
    p.add_argument("--server-url", default="http://127.0.0.1:8001/translate")
    p.add_argument("--engine", default="core")
    p.add_argument("--mirror-rate", type=float, default=0.3)
    p.add_argument("--min-count", type=int, default=1)
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    counter: Counter[str] = Counter()
    for rec in iter_jsonl(Path(args.input)):
        sentence = rec.get("sentence", "")
        for token in _TOKEN.findall(sentence.lower()):
            counter[token] += 1

    items = [w for w, c in counter.items() if c >= args.min_count]
    items.sort(key=lambda w: (-counter[w], w))
    if args.limit:
        items = items[: args.limit]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_tsv = Path(args.output_tsv)

    dictionary = {}
    for word in items:
        row = (
            translate_word_api(word, args.mirror_rate, args.engine)
            if args.mode == "api"
            else translate_word_server(word, args.mirror_rate, args.engine, args.server_url)
        )
        if not row:
            continue
        dictionary[word] = {
            "zyntalic": row.get("target", ""),
            "count": counter[word],
        }

    out_path.write_text(json.dumps(dictionary, ensure_ascii=False, indent=2), encoding="utf-8")

    with out_tsv.open("w", encoding="utf-8") as f:
        f.write("english\tzyntalic\tcount\n")
        for word, data in dictionary.items():
            f.write(f"{word}\t{data['zyntalic']}\t{data['count']}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
