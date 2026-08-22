import json

from zyntalic import cli


def _rows(*_args, **_kwargs):
    return [
        {
            "source": "I see the river.",
            "target": "zyn tal. ⟦ctx:test⟧",
            "anchors": [["Dante_DivineComedy", 0.6], ["Spinoza_Ethics", 0.4]],
            "engine": "core",
        }
    ]


def test_pretty_output_exposes_source_target_and_weights(monkeypatch, capsys):
    monkeypatch.setattr(cli, "translate_text", _rows)
    assert cli.main(["translate", "I see the river."]) == 0
    output = capsys.readouterr().out
    assert "SOURCE" in output
    assert "ZYNTALIC" in output
    assert "Dante_DivineComedy" in output
    assert "60.00%" in output


def test_output_directory_splits_records(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "translate_text", _rows)
    output_dir = tmp_path / "compiled"
    assert cli.main(["translate", "I see the river.", "--output-dir", str(output_dir)]) == 0
    row = json.loads((output_dir / "0001.json").read_text(encoding="utf-8"))
    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert row["target"].startswith("zyn tal")
    assert manifest["files"] == ["0001.json"]
