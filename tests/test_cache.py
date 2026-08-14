from __future__ import annotations

import json
import sqlite3

import pytest

import zyntalic.utils.cache as cache


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    original_initialized = cache._initialized
    cache.close_cache()
    monkeypatch.setattr(cache, "CACHE_PATH", tmp_path / "translations.sqlite3")
    monkeypatch.setattr(cache, "LEGACY_CACHE_PATH", tmp_path / "translations.json")
    monkeypatch.setattr(cache, "_initialized", False)
    yield
    cache.close_cache()
    cache._initialized = original_initialized


def test_translation_and_response_cache_round_trip(isolated_cache):
    options = {"register": " formal ", "empty": "", "ignored": None}
    entry = cache.put_cached_translation(
        " source ",
        "target",
        "core",
        0.3,
        anchors=[["order", 1.0]],
        embedding=[0.1, 0.2],
        options=options,
    )

    assert entry["options"] == {"register": "formal"}
    assert cache.get_cached_translation("source", "core", 0.3, options)["target"] == "target"
    assert cache.get_cached_translation("missing", "core", 0.3) is None

    rows = [{"source": "one", "target": "vez", "engine": "core"}]
    stored = cache.put_cached_response("one", rows, "core", 0.3)
    rows[0]["target"] = "mutated"
    assert stored[0]["target"] == "vez"
    assert cache.get_cached_response("one", "core", 0.3) == stored
    assert cache.cache_info()["entries"] == 2

    cache.save_cache()
    cache.close_cache()
    assert cache.cache_size() == 2


def test_invalid_payloads_are_cache_misses(isolated_cache):
    cache.init_cache()
    connection = sqlite3.connect(cache.CACHE_PATH)
    try:
        connection.execute(
            "INSERT INTO cache_entries(cache_key, payload, updated_at) VALUES (?, ?, ?)",
            ("broken-json", "{", "now"),
        )
        response_key = cache._key("bad", "core", 0.3, namespace="response")
        connection.execute(
            "INSERT INTO cache_entries(cache_key, payload, updated_at) VALUES (?, ?, ?)",
            (response_key, json.dumps({"rows": ["not-a-row"]}), "now"),
        )
        connection.commit()
    finally:
        connection.close()

    assert cache._get_payload("broken-json") is None
    assert cache.get_cached_response("bad", "core", 0.3) is None


def test_legacy_json_is_migrated_once(isolated_cache):
    cache.LEGACY_CACHE_PATH.write_text(
        json.dumps(
            {
                "valid": {
                    "source": "legacy",
                    "target": "vez",
                    "engine": "core",
                    "mirror_rate": 0.3,
                },
                "invalid": "skip-me",
            }
        ),
        encoding="utf-8",
    )

    cache.init_cache()
    assert cache.cache_size() == 1
    assert cache.get_cached_response("legacy", "core", 0.3)[0]["target"] == "vez"
    cache.init_cache()
    assert cache.cache_size() == 1
