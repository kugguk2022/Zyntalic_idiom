"""Assemble the Zyntalic anchor lexicons into a Hugging Face dataset directory.

Reads the packaged lexicons from ``zyntalic/resources/lexicon`` and writes:

  out/
    README.md          data card (copied from this directory)
    lexicon.jsonl      one row per (anchor, category, word)
    motifs.jsonl       one row per (anchor, motif pair)
    raw/<anchor>.json  the original per-anchor files, unchanged

Usage:
    python huggingface/dataset/build_dataset.py --out huggingface/dataset/out
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEXICON_DIR = REPO_ROOT / "zyntalic" / "resources" / "lexicon"
DATA_CARD = Path(__file__).resolve().parent / "README.md"

WORD_CATEGORIES = ("nouns", "verbs", "adjectives")


def _anchor_files() -> list[Path]:
    return sorted(path for path in LEXICON_DIR.glob("*.json"))


def build(out_dir: Path) -> dict[str, int]:
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    word_rows: list[dict[str, object]] = []
    motif_rows: list[dict[str, object]] = []

    for path in _anchor_files():
        anchor = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        shutil.copyfile(path, raw_dir / path.name)

        for category in WORD_CATEGORIES:
            for rank, word in enumerate(data.get(category, []) or []):
                word_rows.append(
                    {
                        "anchor": anchor,
                        "category": category[:-1],  # nouns -> noun
                        "word": word,
                        "rank": rank,
                    }
                )

        for motif in data.get("motifs", []) or []:
            if isinstance(motif, (list, tuple)) and len(motif) >= 2:
                motif_rows.append({"anchor": anchor, "pole_a": motif[0], "pole_b": motif[1]})

    _write_jsonl(out_dir / "lexicon.jsonl", word_rows)
    _write_jsonl(out_dir / "motifs.jsonl", motif_rows)

    if DATA_CARD.exists():
        shutil.copyfile(DATA_CARD, out_dir / "README.md")

    return {
        "anchors": len(_anchor_files()),
        "words": len(word_rows),
        "motifs": len(motif_rows),
    }


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "out",
        help="Directory to write the dataset into.",
    )
    args = parser.parse_args()

    stats = build(args.out)
    print(
        f"Wrote {stats['words']} words and {stats['motifs']} motif pairs "
        f"from {stats['anchors']} anchors to {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
