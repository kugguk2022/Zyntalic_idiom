from pathlib import Path

from zyntalic import embeddings


def test_embedding_cache_is_repository_local():
    repository_root = Path(embeddings.__file__).resolve().parents[1]

    assert embeddings._CACHE_DIR == repository_root / "data" / "cache"


def test_default_flush_defers_full_cache_rewrite(monkeypatch):
    writes = []
    monkeypatch.setattr(embeddings, "_CACHE_FLUSH_EVERY", 0)
    monkeypatch.setattr(embeddings, "_WORD_DIRTY", 1)
    monkeypatch.setattr(embeddings, "_CONTEXT_DIRTY", 1)
    monkeypatch.setattr(embeddings, "_write_cache", lambda path, payload: writes.append(path))

    embeddings._flush_cache()

    assert writes == []
    assert embeddings._WORD_DIRTY == 1
    assert embeddings._CONTEXT_DIRTY == 1


def test_forced_flush_persists_both_embedding_caches(monkeypatch):
    writes = []
    monkeypatch.setattr(embeddings, "_CACHE_FLUSH_EVERY", 0)
    monkeypatch.setattr(embeddings, "_WORD_DIRTY", 1)
    monkeypatch.setattr(embeddings, "_CONTEXT_DIRTY", 1)
    monkeypatch.setattr(embeddings, "_write_cache", lambda path, payload: writes.append(path))

    embeddings._flush_cache(force=True)

    assert writes == [embeddings._WORD_CACHE_PATH, embeddings._CONTEXT_CACHE_PATH]
    assert embeddings._WORD_DIRTY == 0
    assert embeddings._CONTEXT_DIRTY == 0
