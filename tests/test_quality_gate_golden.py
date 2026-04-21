import hashlib
import json
import re
from pathlib import Path

from zyntalic.translator import translate_text

PROMPTS_PATH = Path("data/fixtures/golden_prompts.json")
GOLDEN_PATH = Path("data/fixtures/golden_core_hashes.json")


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _render(prompt: str) -> str:
    rows = translate_text(prompt, mirror_rate=0.2, engine="core")
    assert rows, f"No translation rows for prompt: {prompt}"
    return rows[0]["target"]


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _surface_and_ctx(target: str):
    if "⟦ctx:" not in target:
        return target.strip(), ""
    surface, _, tail = target.partition("⟦ctx:")
    return surface.strip(), f"⟦ctx:{tail}"


def test_golden_core_hashes_and_quality_gate(monkeypatch):
    # Force deterministic fallback path so this gate is stable in CI/dev machines.
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    monkeypatch.setenv("ZYNTALIC_NLP", "none")

    prompts = _load_json(PROMPTS_PATH)
    golden = _load_json(GOLDEN_PATH)
    expected = {item["prompt"]: item["sha256"] for item in golden}

    mismatches = []
    script_mixed_count = 0

    for prompt in prompts:
        target = _render(prompt)
        digest = _sha256(target)
        expected_digest = expected.get(prompt)
        if expected_digest != digest:
            mismatches.append((prompt, expected_digest, digest))

        surface, ctx = _surface_and_ctx(target)
        assert ctx.startswith("⟦ctx:"), f"Missing context tail for prompt: {prompt}"
        assert ctx.endswith("⟧"), f"Malformed context tail for prompt: {prompt}"
        assert "order=SOVC" in ctx, f"Missing SOVC tag for prompt: {prompt}"
        assert re.search(r"roles=S[01]\|O[01]\|V[01]\|C[01]", ctx), (
            f"Missing role profile tag for prompt: {prompt}"
        )

        has_hangul_in_ctx = "han=" in ctx and any("\uac00" <= ch <= "\ud7af" for ch in ctx)
        has_latin_surface = any(("a" <= ch.lower() <= "z") for ch in surface)
        if has_hangul_in_ctx and has_latin_surface:
            script_mixed_count += 1

    # Require at least 30% of prompts to produce Latin surface output with Hangul in ctx.
    assert script_mixed_count >= max(1, int(len(prompts) * 0.30)), (
        f"Mixed-script coverage too low: {script_mixed_count}/{len(prompts)}"
    )

    if mismatches:
        sample = mismatches[:5]
        raise AssertionError(
            "Golden snapshot drift detected for core engine. "
            "If intentional, regenerate data/fixtures/golden_core_hashes.json. "
            f"Mismatches(sample): {sample}"
        )


def test_golden_files_are_consistent():
    prompts = _load_json(PROMPTS_PATH)
    golden = _load_json(GOLDEN_PATH)
    prompt_set = set(prompts)
    golden_prompt_set = {item["prompt"] for item in golden}

    assert prompt_set == golden_prompt_set, (
        "Prompt fixture and golden hashes are out of sync. "
        "Update both files together."
    )
