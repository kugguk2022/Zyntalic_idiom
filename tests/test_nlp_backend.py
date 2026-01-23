import importlib


def test_split_sentences_fallback(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    import zyntalic.nlp as nlp
    importlib.reload(nlp)

    text = "Hello world. This is a test!"
    parts = nlp.split_sentences(text)
    assert parts == ["Hello world.", "This is a test!"]


def test_first_lemma_fallback(monkeypatch):
    monkeypatch.setenv("ZYNTALIC_NLP", "none")
    import zyntalic.nlp as nlp
    importlib.reload(nlp)

    assert nlp.first_lemma("Running fast") == "running"
