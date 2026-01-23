import importlib


def test_translate_batch(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    import zyntalic.translator as translator
    importlib.reload(translator)

    texts = ["Hello world.", "Love is patient."]
    rows = translator.translate_batch(texts, mirror_rate=0.2, engine="core", flatten=False)
    assert len(rows) == 2
    assert all(isinstance(group, list) for group in rows)
    assert rows[0][0]["target"]

    flat = translator.translate_batch(texts, mirror_rate=0.2, engine="core", flatten=True)
    assert len(flat) == sum(len(g) for g in rows)
