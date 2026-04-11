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
    assert "evidentiality=inferential" in row["target"]
    assert "frames=A:Sunzi_ArtOfWar|B:Dostoevsky_BrothersKaramazov" in row["target"]
    assert sidecar["pivot"] in {"converge", "diverge"}
    assert sidecar["evidentiality"] == "inferential"
    assert sidecar["register"] == "formal"
    assert sidecar["dialect"] == "standard"
    assert sidecar["anchor_mode"] == "auto"
    assert sidecar["selected_anchors"] == [
        "Sunzi_ArtOfWar",
        "Dostoevsky_BrothersKaramazov",
    ]
    assert sidecar["scope_signature"]
    assert len(sidecar["anchor_weights"]) > 0
    assert all("name" in item and "weight" in item for item in sidecar["anchor_weights"])
    assert sidecar["tokens"]
    assert sidecar["tokens"][0]["surface"] == "War"

    frames = sidecar["frames"]
    assert [frame["id"] for frame in frames] == ["A", "B"]
    assert frames[0]["anchor"] == "Sunzi_ArtOfWar"
    assert frames[1]["anchor"] == "Dostoevsky_BrothersKaramazov"


def test_translate_text_scope_controls_change_target(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    importlib.reload(translator)

    base = translator.translate_text(
        "Silence remembers time.",
        mirror_rate=0.2,
        engine="core",
    )[0]["target"]
    scoped = translator.translate_text(
        "Silence remembers time.",
        mirror_rate=0.2,
        engine="core",
        config={
            "register": "literary",
            "dialect": "northern",
        },
    )[0]

    assert scoped["target"] != base
    assert "register=literary" in scoped["target"]
    assert "dialect=northern" in scoped["target"]
    assert scoped["sidecar"]["register"] == "literary"
    assert scoped["sidecar"]["dialect"] == "northern"


def test_transformer_engine_respects_explicit_frame_selection(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    importlib.reload(translator)

    row = translator.translate_text(
        "Order remembers chaos.",
        mirror_rate=0.2,
        engine="transformer",
        config={
            "anchor_mode": "manual",
            "selected_anchors": ["Sunzi_ArtOfWar", "Plato_Republic"],
        },
    )[0]

    sidecar = row["sidecar"]
    assert [frame["anchor"] for frame in sidecar["frames"]] == [
        "Sunzi_ArtOfWar",
        "Plato_Republic",
    ]
    assert [item["name"] for item in sidecar["anchor_weights"][:2]] == [
        "Sunzi_ArtOfWar",
        "Plato_Republic",
    ]
    assert sidecar["anchor_mode"] == "manual"
    assert sidecar["selected_anchors"] == ["Sunzi_ArtOfWar", "Plato_Republic"]


def test_no_frame_selection_keeps_frame_metadata_empty(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    importlib.reload(translator)

    row = translator.translate_text(
        "Order remembers chaos.",
        mirror_rate=0.2,
        engine="core",
        config={
            "frame_a": "",
            "frame_b": "",
        },
    )[0]

    assert row["sidecar"]["frames"] == []
    assert row["sidecar"]["anchor_mode"] == "auto"


def test_neutral_anchor_mode_disables_anchor_inference(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    importlib.reload(translator)

    row = translator.translate_text(
        "Order remembers chaos.",
        mirror_rate=0.2,
        engine="core",
        config={
            "anchor_mode": "neutral",
            "selected_anchors": ["Sunzi_ArtOfWar", "Plato_Republic"],
        },
    )[0]

    assert row["sidecar"]["anchor_mode"] == "neutral"
    assert row["sidecar"]["frames"] == []
    assert row["sidecar"]["anchor_weights"] == []


def test_manual_anchor_mode_accepts_more_than_two_selected_anchors(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    monkeypatch.setenv("ZYNTALIC_FAST", "1")
    importlib.reload(translator)

    row = translator.translate_text(
        "Order remembers chaos.",
        mirror_rate=0.2,
        engine="core",
        config={
            "anchor_mode": "manual",
            "selected_anchors": [
                "Sunzi_ArtOfWar",
                "Plato_Republic",
                "Spinoza_Ethics",
            ],
        },
    )[0]

    sidecar = row["sidecar"]
    assert sidecar["anchor_mode"] == "manual"
    assert sidecar["selected_anchors"] == [
        "Sunzi_ArtOfWar",
        "Plato_Republic",
        "Spinoza_Ethics",
    ]
    assert [item["name"] for item in sidecar["anchor_weights"][:3]] == [
        "Sunzi_ArtOfWar",
        "Plato_Republic",
        "Spinoza_Ethics",
    ]


def test_rule1_enforces_context_tail_for_non_reverse_engine():
    target = translator._enforce_target_rules("surface only", "seed text", "core")
    assert "⟦ctx:" in target
    assert target.endswith("⟧")


def test_rule1_validation_flags_multiple_context_tails():
    bad = "alpha ⟦ctx:han=가나⟧ beta ⟦ctx:han=다라⟧"
    warnings = translator._validate_target_rules(bad, "core")
    assert "multiple_context_tails" in warnings


def test_rule1_enforces_sovc_and_roles_tags():
    target = translator._enforce_target_rules("surface only", "I see the river at night.", "core")
    assert "order=SOVC" in target
    assert "roles=S1|O1|V1|C1" in target


def test_rule1_validation_flags_missing_roles_and_order():
    bad = "surface ⟦ctx:han=가나⟧"
    warnings = translator._validate_target_rules(bad, "core")
    assert "missing_or_invalid_order_tag" in warnings
    assert "missing_or_invalid_roles_tag" in warnings
