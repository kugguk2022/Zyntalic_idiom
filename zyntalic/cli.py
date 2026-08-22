# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from .translator import translate_text

def _read_stdin() -> str:
    return sys.stdin.read()

def cmd_translate(args: argparse.Namespace) -> int:
    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
    else:
        text = args.text if args.text is not None else _read_stdin()
    rows = translate_text(text, mirror_rate=args.mirror_rate, engine=args.engine)
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        files = []
        for index, row in enumerate(rows, 1):
            path = output_dir / f"{index:04d}.json"
            path.write_text(json.dumps(row, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            files.append(path.name)
        (output_dir / "manifest.json").write_text(
            json.dumps({"source": args.input, "count": len(rows), "files": files}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Exported {len(rows)} records to {output_dir}", file=sys.stderr)
        return 0
    if args.format == "plain":
        for r in rows:
            sys.stdout.write(r["target"] + ("\n" if not r["target"].endswith("\n") else ""))
        return 0

    if args.format == "json":
        sys.stdout.write(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
        return 0

    if args.format == "pretty":
        for index, row in enumerate(rows, 1):
            print(f"\n[{index}] SOURCE\n{row.get('source', '')}")
            print(f"\n    ZYNTALIC\n{row.get('target', '')}")
            anchors = row.get("anchors") or []
            if anchors:
                print("\n    ANCHOR WEIGHTS")
                for name, weight in anchors:
                    print(f"    {name:<30} {float(weight):6.2%}")
        return 0

    # jsonl
    for r in rows:
        sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0

def cmd_version(_: argparse.Namespace) -> int:
    from . import __version__
    print(__version__)
    return 0

def cmd_web(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print('Web support is not installed. Run: pip install "zyntalic[web]"', file=sys.stderr)
        return 2
    os.environ["ZYNTALIC_ALLOW_UNAUTHENTICATED_LOCAL"] = "1"
    uvicorn.run("apps.web.app:app", host=args.host, port=args.port, reload=False)
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zyntalic", description="Zyntalic synthetic-language toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("translate", help="Translate text to Zyntalic")
    t.add_argument("text", nargs="?", default=None, help="Text to translate (or stdin if omitted)")
    t.add_argument("--engine", choices=["core","chiasmus"], default="core")
    t.add_argument("--mirror-rate", type=float, default=0.8)
    t.add_argument("--format", choices=["pretty","jsonl","json","plain"], default="pretty")
    t.add_argument("--input", help="Read UTF-8 source text from a file")
    t.add_argument("--output-dir", help="Write one JSON record per translated sentence")
    t.set_defaults(func=cmd_translate)

    v = sub.add_parser("version", help="Print version")
    v.set_defaults(func=cmd_version)

    w = sub.add_parser("web", help="Launch the local dual-display compiler")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=8000)
    w.set_defaults(func=cmd_web)

    return p

def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
