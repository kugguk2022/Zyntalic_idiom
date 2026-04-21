#!/usr/bin/env python3
"""
Batch translate sentences to Zyntalic.

Supports:
- api: in-process Python API (fastest)
- server: HTTP server at /translate
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Iterable
from pathlib import Path

try:
    import requests
except Exception:
    requests = None


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def translate_api(sentences: list[str], mirror_rate: float, engine: str) -> list[dict]:
    from zyntalic import translator
    translator.warm_translation_pipeline()
    rows = translator.translate_batch(sentences, mirror_rate=mirror_rate, engine=engine, flatten=True)
    return rows


def translate_server(sentences: list[str], mirror_rate: float, engine: str, url: str) -> list[dict]:
    if requests is None:
        raise SystemExit("requests not available. Install with: pip install -e .[data]")

    rows: list[dict] = []
    for s in sentences:
        payload = {"text": s, "mirror_rate": mirror_rate, "engine": engine}
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if "rows" in data and data["rows"]:
            rows.append(data["rows"][0])
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", default="data_generation/sentences/sentences.jsonl")
    p.add_argument("--output", default="data_generation/sentences/translations.jsonl")
    p.add_argument("--mode", choices=["api", "server"], default="api")
    p.add_argument("--server-url", default="http://127.0.0.1:8001/translate")
    p.add_argument("--engine", default="core")
    p.add_argument("--mirror-rate", type=float, default=0.3)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--sleep", type=float, default=0.0)
    p.add_argument("--batch-size", type=int, default=32)
    args = p.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    buffer = []
    meta = []
    with out_path.open("w", encoding="utf-8") as f:
        for rec in iter_jsonl(in_path):
            sentence = rec.get("sentence", "").strip()
            if not sentence:
                continue
            buffer.append(sentence)
            meta.append((rec.get("source_id"), rec.get("source_path")))

            if len(buffer) >= args.batch_size:
                rows = (
                    translate_api(buffer, args.mirror_rate, args.engine)
                    if args.mode == "api"
                    else translate_server(buffer, args.mirror_rate, args.engine, args.server_url)
                )
                for row, (source_id, source_path) in zip(rows, meta):
                    row["source_id"] = source_id
                    row["source_path"] = source_path
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
                    if args.limit and count >= args.limit:
                        return 0
                buffer = []
                meta = []
                if args.sleep:
                    time.sleep(args.sleep)

        if buffer:
            rows = (
                translate_api(buffer, args.mirror_rate, args.engine)
                if args.mode == "api"
                else translate_server(buffer, args.mirror_rate, args.engine, args.server_url)
            )
            for row, (source_id, source_path) in zip(rows, meta):
                row["source_id"] = source_id
                row["source_path"] = source_path
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
                if args.limit and count >= args.limit:
                    break

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
