import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "report_golden_drift.py"
SPEC = importlib.util.spec_from_file_location("report_golden_drift", MODULE_PATH)
assert SPEC and SPEC.loader
report_golden_drift = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_golden_drift)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_report_records_old_and_current_hashes_without_changing_fixtures(tmp_path):
    prompts = tmp_path / "prompts.json"
    golden = tmp_path / "golden.json"
    prompts.write_text(json.dumps(["mixed", "latin"]), encoding="utf-8")
    golden.write_text(
        json.dumps(
            [
                {"prompt": "mixed", "sha256": _sha256("old")},
                {"prompt": "latin", "sha256": _sha256("latin only")},
            ]
        ),
        encoding="utf-8",
    )
    before = golden.read_bytes()

    report = report_golden_drift.build_report(
        prompts,
        golden,
        lambda prompt: "latin 한글 ⟦ctx:test⟧" if prompt == "mixed" else "latin only",
    )

    assert report["prompt_count"] == 2
    assert report["mismatch_count"] == 1
    assert report["mixed_script_count"] == 1
    assert report["required_mixed_script_count"] == 1
    assert report["mismatches"] == [
        {
            "prompt": "mixed",
            "expected_sha256": _sha256("old"),
            "current_sha256": _sha256("latin 한글 ⟦ctx:test⟧"),
        }
    ]
    assert golden.read_bytes() == before


def test_cli_refuses_to_replace_reviewed_golden_fixture(tmp_path):
    prompts = tmp_path / "prompts.json"
    golden = tmp_path / "golden.json"
    prompts.write_text("[]", encoding="utf-8")
    golden.write_text("[]", encoding="utf-8")

    with pytest.raises(SystemExit):
        report_golden_drift.main(
            ["--prompts", str(prompts), "--golden", str(golden), "--output", str(golden)]
        )

    assert golden.read_text(encoding="utf-8") == "[]"


def test_cli_prints_a_machine_readable_report_without_writing(tmp_path, capsys):
    prompts = tmp_path / "prompts.json"
    golden = tmp_path / "golden.json"
    prompts.write_text("[]", encoding="utf-8")
    golden.write_text("[]", encoding="utf-8")

    assert report_golden_drift.main(
        ["--prompts", str(prompts), "--golden", str(golden)]
    ) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == 1
    assert report["prompt_count"] == 0
    assert report["mismatches"] == []
