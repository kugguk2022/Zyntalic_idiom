import zyntalic.core as core


def test_staged_generator_matches_legacy(monkeypatch):
    seed = "rule3-stage-equivalence"

    monkeypatch.setenv("ZYNTALIC_USE_STAGED_GENERATOR", "1")
    monkeypatch.delenv("ZYNTALIC_STAGE_FORCE_FAIL", raising=False)
    staged = core.generate_entry(seed, mirror_rate=0.2)

    monkeypatch.setenv("ZYNTALIC_USE_STAGED_GENERATOR", "0")
    legacy = core.generate_entry(seed, mirror_rate=0.2)

    assert staged["word"] == legacy["word"]
    assert staged["meaning"] == legacy["meaning"]
    assert staged["sentence"] == legacy["sentence"]


def test_staged_generator_falls_back_deterministically(monkeypatch):
    seed = "rule3-stage-fallback"

    monkeypatch.setenv("ZYNTALIC_USE_STAGED_GENERATOR", "1")
    monkeypatch.setenv("ZYNTALIC_STAGE_FORCE_FAIL", "1")
    fallback_output = core.generate_entry(seed, mirror_rate=0.2)

    monkeypatch.setenv("ZYNTALIC_USE_STAGED_GENERATOR", "0")
    monkeypatch.delenv("ZYNTALIC_STAGE_FORCE_FAIL", raising=False)
    legacy_output = core.generate_entry(seed, mirror_rate=0.2)

    assert fallback_output["word"] == legacy_output["word"]
    assert fallback_output["meaning"] == legacy_output["meaning"]
    assert fallback_output["sentence"] == legacy_output["sentence"]
