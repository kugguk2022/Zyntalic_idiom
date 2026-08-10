from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from apps.web.app import app


def _unique_text() -> str:
    return f"The river remembers {uuid.uuid4().hex}. The moon answers quietly."


def test_legacy_health_and_translate_contracts_are_preserved():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"ok": True}
        response = client.post("/translate", json={"text": _unique_text()})

    assert response.status_code == 200
    assert set(response.json()) == {"rows", "cached"}
    assert response.json()["rows"]


def test_http_errors_are_not_rewritten_as_internal_errors():
    with TestClient(app) as client:
        empty = client.post("/translate", json={"text": "   "})
        invalid_engine = client.post("/v1/translate", json={"text": "Hello", "engine": "unknown"})

    assert empty.status_code == 400
    assert invalid_engine.status_code == 422


def test_v1_response_has_metadata_and_exact_request_cache():
    payload = {"text": _unique_text(), "engine": "core", "mirror_rate": 0.3}
    with TestClient(app) as client:
        first = client.post("/v1/translate", json=payload, headers={"X-Request-ID": "test-123"})
        second = client.post("/v1/translate", json=payload)

    assert first.status_code == 200
    assert first.json()["request_id"] == "test-123"
    assert first.headers["X-Request-ID"] == "test-123"
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert first.json()["rows"] == second.json()["rows"]
    assert len(first.json()["rows"]) == 2


def test_batch_endpoint_preserves_order_and_reports_cache_hits():
    text = _unique_text()
    with TestClient(app) as client:
        response = client.post(
            "/v1/translate/batch",
            json={"texts": [text, text], "engine": "core"},
        )

    body = response.json()
    assert response.status_code == 200
    assert body["items"] == 2
    assert [item["index"] for item in body["results"]] == [0, 1]
    assert body["results"][0]["cached"] is False
    assert body["results"][1]["cached"] is True
    assert body["cache_hits"] == 1


def test_extract_preserves_unicode_text():
    with TestClient(app) as client:
        response = client.post(
            "/v1/extract",
            files={"file": ("sample.txt", "Olá — Καλημέρα — 안녕하세요".encode(), "text/plain")},
        )

    assert response.status_code == 200
    assert response.json()["text"] == "Olá — Καλημέρα — 안녕하세요"
    assert response.json()["characters"] == len(response.json()["text"])


def test_health_v1_exposes_operational_limits_and_cache_backend():
    with TestClient(app) as client:
        response = client.get("/v1/health")

    body = response.json()
    assert response.status_code == 200
    assert body["ready"] is True
    assert body["cache"]["backend"] == "sqlite-wal"
    assert body["limits"]["batch_items"] >= 1
