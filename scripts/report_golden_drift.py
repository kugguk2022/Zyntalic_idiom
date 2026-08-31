"""Report current core-output drift without rewriting reviewed golden fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable
from pathlib import Path

DEFAULT_PROMPTS = Path("data/fixtures/golden_prompts.json")
DEFAULT_GOLDEN = Path("data/fixtures/golden_core_hashes.json")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _surface(target: str) -> str:
    return target.partition("⟦ctx:")[0].strip()


def _is_mixed_script(target: str) -> bool:
    surface = _surface(target)
    has_hangul = any("\uac00" <= char <= "\ud7af" for char in surface)
    has_latin = any("a" <= char.lower() <= "z" for char in surface)
    return has_hangul and has_latin


def build_report(
    prompts_path: Path,
    golden_path: Path,
    render: Callable[[str], str],
) -> dict[str, object]:
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    golden_rows = json.loads(golden_path.read_text(encoding="utf-8"))
    expected = {row["prompt"]: row["sha256"] for row in golden_rows}

    mismatches = []
    mixed_count = 0
    for prompt in prompts:
        target = render(prompt)
        current_sha = _sha256(target)
        expected_sha = expected.get(prompt)
        mixed_count += int(_is_mixed_script(target))
        if current_sha != expected_sha:
            mismatches.append(
                {
                    "prompt": prompt,
                    "expected_sha256": expected_sha,
                    "current_sha256": current_sha,
                }
            )

    return {
        "schema_version": 1,
        "prompt_count": len(prompts),
        "mismatch_count": len(mismatches),
        "mixed_script_count": mixed_count,
        "required_mixed_script_count": max(1, int(len(prompts) * 0.30)),
        "mismatches": mismatches,
    }


def _render(prompt: str) -> str:
    from zyntalic.translator import translate_text

    rows = translate_text(prompt, mirror_rate=0.2, engine="core")
    if not rows:
        raise RuntimeError(f"no translation rows for prompt: {prompt}")
    return rows[0]["target"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", type=Path, default=DEFAULT_PROMPTS)
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    report = build_report(args.prompts, args.golden, _render)
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        if args.output.resolve() == args.golden.resolve():
            parser.error("refusing to overwrite the reviewed golden fixture")
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
