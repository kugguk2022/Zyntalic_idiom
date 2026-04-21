from __future__ import annotations

import argparse
import json
import sys

from .translator import translate_text


def _read_stdin() -> str:
    return sys.stdin.read()

def cmd_translate(args: argparse.Namespace) -> int:
    text = args.text if args.text is not None else _read_stdin()
    rows = translate_text(text, mirror_rate=args.mirror_rate, engine=args.engine)
    if args.format == "plain":
        for r in rows:
            sys.stdout.write(r["target"] + ("\n" if not r["target"].endswith("\n") else ""))
        return 0

    if args.format == "json":
        sys.stdout.write(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
        return 0

    # jsonl
    for r in rows:
        sys.stdout.write(json.dumps(r, ensure_ascii=False) + "\n")
    return 0

def cmd_version(_: argparse.Namespace) -> int:
    from . import __version__
    print(__version__)
    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="zyntalic", description="Zyntalic synthetic-language toolkit")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("translate", help="Translate text to Zyntalic")
    t.add_argument("text", nargs="?", default=None, help="Text to translate (or stdin if omitted)")
    t.add_argument("--engine", choices=["core","chiasmus"], default="core")
    t.add_argument("--mirror-rate", type=float, default=0.8)
    t.add_argument("--format", choices=["jsonl","json","plain"], default="jsonl")
    t.set_defaults(func=cmd_translate)

    v = sub.add_parser("version", help="Print version")
    v.set_defaults(func=cmd_version)

    return p

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))

if __name__ == "__main__":
    raise SystemExit(main())
