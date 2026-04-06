import importlib

import zyntalic.translator as translator


def test_translate_text_attaches_sidecar(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    importlib.reload(translator)

    row = translator.translate_text(
        "War remembers peace.",
        mirror_rate=0.2,
        engine="core",
        config={
            "evidentiality": "inferential",
            "frame_a": "Sunzi_ArtOfWar",
            "frame_b": "Dostoevsky_BrothersKaramazov",
        },
    )[0]

    sidecar = row.get("sidecar")
    assert sidecar, "Expected sidecar metadata on translation rows"
    assert "sigil" in sidecar
    assert "⟦ctx:" in row["target"], "Legacy context tail should remain intact"
    assert sidecar["pivot"] == "neutral"
    assert sidecar["evidentiality"] == "inferential"
    assert len(sidecar["anchor_weights"]) > 0
    assert all("name" in item and "weight" in item for item in sidecar["anchor_weights"])

    frames = sidecar["frames"]
    assert [frame["id"] for frame in frames] == ["A", "B"]
    assert frames[0]["anchor"] == "Sunzi_ArtOfWar"
    assert frames[1]["anchor"] == "Dostoevsky_BrothersKaramazov"
