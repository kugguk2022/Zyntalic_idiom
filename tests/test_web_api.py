from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import apps.web.app as web_app
from apps.web.app import SlidingWindowRateLimiter, app

API_KEY = "test-api-key"
AUTH_HEADERS = {"X-API-Key": API_KEY}


@pytest.fixture(autouse=True)
def isolated_api_security(monkeypatch):
    monkeypatch.setattr(web_app, "API_KEY", API_KEY)
    monkeypatch.setattr(web_app, "ALLOW_UNAUTHENTICATED_LOCAL", False)
    monkeypatch.setattr(web_app, "rate_limiter", SlidingWindowRateLimiter(1000))


def _unique_text() -> str:
    return f"The river remembers {uuid.uuid4().hex}. The moon answers quietly."


def test_legacy_health_and_translate_contracts_are_preserved():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"ok": True}
        response = client.post(
            "/translate", json={"text": _unique_text()}, headers=AUTH_HEADERS
        )

    assert response.status_code == 200
    assert set(response.json()) == {"rows", "cached"}
    assert response.json()["rows"]


def test_http_errors_are_not_rewritten_as_internal_errors():
    with TestClient(app) as client:
        empty = client.post(
            "/translate", json={"text": "   "}, headers=AUTH_HEADERS
        )
        invalid_engine = client.post(
            "/v1/translate",
            json={"text": "Hello", "engine": "unknown"},
            headers=AUTH_HEADERS,
        )

    assert empty.status_code == 400
    assert invalid_engine.status_code == 422


def test_v1_response_has_metadata_and_exact_request_cache():
    payload = {"text": _unique_text(), "engine": "core", "mirror_rate": 0.3}
    with TestClient(app) as client:
        first = client.post(
            "/v1/translate",
            json=payload,
            headers={**AUTH_HEADERS, "X-Request-ID": "test-123"},
        )
        second = client.post("/v1/translate", json=payload, headers=AUTH_HEADERS)

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
            headers=AUTH_HEADERS,
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
            headers=AUTH_HEADERS,
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
    assert body["limits"]["requests_per_minute"] >= 1


def test_expensive_routes_fail_closed_and_require_valid_api_key(monkeypatch):
    with TestClient(app) as client:
        missing = client.post("/v1/translate", json={"text": "Hello"})
        invalid = client.post(
            "/v1/translate",
            json={"text": "Hello"},
            headers={"X-API-Key": "wrong"},
        )
        health = client.get("/v1/health")

        monkeypatch.setattr(web_app, "API_KEY", "")
        unconfigured = client.post(
            "/v1/translate", json={"text": "Hello"}, headers=AUTH_HEADERS
        )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert invalid.headers["WWW-Authenticate"] == "ApiKey"
    assert health.status_code == 200
    assert unconfigured.status_code == 503


def test_loopback_requests_do_not_require_an_api_key():
    request = web_app.Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/upload",
            "headers": [],
            "client": ("127.0.0.1", 53289),
            "server": ("127.0.0.1", 8000),
            "scheme": "http",
            "query_string": b"",
        }
    )
    web_app.require_api_access(request, supplied_key=None)


def test_forwarded_loopback_header_does_not_bypass_api_key(monkeypatch):
    monkeypatch.setattr(web_app, "API_KEY", "test-api-key")
    request = web_app.Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/upload",
            "headers": [(b"x-forwarded-for", b"127.0.0.1")],
            "client": ("203.0.113.10", 53289),
            "server": ("127.0.0.1", 8000),
            "scheme": "http",
            "query_string": b"",
        }
    )
    with pytest.raises(web_app.HTTPException) as denied:
        web_app.require_api_access(request, supplied_key=None)
    assert denied.value.status_code == 401


def test_rate_limit_returns_retry_after(monkeypatch):
    monkeypatch.setattr(web_app, "rate_limiter", SlidingWindowRateLimiter(1))
    with TestClient(app) as client:
        first = client.post(
            "/v1/extract",
            files={"file": ("one.txt", b"one", "text/plain")},
            headers=AUTH_HEADERS,
        )
        limited = client.post(
            "/v1/extract",
            files={"file": ("two.txt", b"two", "text/plain")},
            headers=AUTH_HEADERS,
        )

    assert first.status_code == 200
    assert limited.status_code == 429
    assert int(limited.headers["Retry-After"]) >= 1


def test_openapi_contract_is_typed_constrained_and_secured():
    schema = app.openapi()
    components = schema["components"]
    models = components["schemas"]

    protected = {
        "/translate",
        "/upload",
        "/v1/translate",
        "/v1/translate/batch",
        "/v1/extract",
    }
    for path in protected:
        operation = schema["paths"][path]["post"]
        response_schema = operation["responses"]["200"]["content"]["application/json"][
            "schema"
        ]
        assert response_schema
        assert operation["security"] == [{"ZyntalicApiKey": []}]

    engine_schema = models["TranslateRequest"]["properties"]["engine"]
    assert set(engine_schema["enum"]) == {
        "core",
        "transformer",
        "chiasmus",
        "test_suite",
        "reverse",
    }
    texts_schema = models["TranslateBatchRequest"]["properties"]["texts"]
    assert texts_schema["maxItems"] == web_app.MAX_BATCH_ITEMS
    assert "sequentially" in schema["paths"]["/v1/translate/batch"]["post"][
        "description"
    ]


def test_batch_item_limit_is_schema_validation():
    payload = {"texts": ["x"] * (web_app.MAX_BATCH_ITEMS + 1)}
    with TestClient(app) as client:
        response = client.post(
            "/v1/translate/batch", json=payload, headers=AUTH_HEADERS
        )

    assert response.status_code == 422


def test_legacy_extract_and_input_size_limits(monkeypatch):
    with TestClient(app) as client:
        legacy = client.post(
            "/upload",
            files={"file": ("sample.md", b"hello", "text/markdown")},
            headers=AUTH_HEADERS,
        )
        invalid_type = client.post(
            "/v1/extract",
            files={"file": ("sample.exe", b"no", "application/octet-stream")},
            headers=AUTH_HEADERS,
        )
        monkeypatch.setattr(web_app, "MAX_UPLOAD_BYTES", 2)
        oversized = client.post(
            "/v1/extract",
            files={"file": ("sample.txt", b"long", "text/plain")},
            headers=AUTH_HEADERS,
        )

    assert legacy.json() == {"text": "hello"}
    assert invalid_type.status_code == 400
    assert oversized.status_code == 413


def test_text_and_batch_character_limits(monkeypatch):
    monkeypatch.setattr(web_app, "MAX_TEXT_CHARS", 2)
    monkeypatch.setattr(web_app, "MAX_BATCH_CHARS", 3)
    with TestClient(app) as client:
        text = client.post(
            "/v1/translate", json={"text": "long"}, headers=AUTH_HEADERS
        )
        batch = client.post(
            "/v1/translate/batch",
            json={"texts": ["two", "two"]},
            headers=AUTH_HEADERS,
        )

    assert text.status_code == 413
    assert batch.status_code == 413


def test_local_override_and_disabled_rate_limiter(monkeypatch):
    monkeypatch.setattr(web_app, "ALLOW_UNAUTHENTICATED_LOCAL", True)
    monkeypatch.setattr(web_app, "rate_limiter", SlidingWindowRateLimiter(0))
    with TestClient(app) as client:
        response = client.post(
            "/v1/extract", files={"file": ("local.txt", b"local", "text/plain")}
        )

    assert response.status_code == 200


def test_static_routes_and_pdf_cleaning():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/favicon.ico").status_code == 200
        assert client.get("/favicon.svg").status_code == 200
        assert client.get("/index.css").status_code == 200

    raw = "%PDF-1.4\r\n/Author(Someone)\n12\nUseful   Unicode — text\x00\n\n\nSecond line\n%%EOF"
    assert web_app.clean_pdf_text(raw) == "Useful Unicode — text\nSecond line"


def test_pdf_extraction_failures_are_bounded(monkeypatch):
    class Reader:
        def __init__(self, _stream):
            self.is_encrypted = False
            self.pages = [
                SimpleNamespace(extract_text=lambda: "Readable document text"),
                SimpleNamespace(extract_text=lambda: (_ for _ in ()).throw(ValueError("page"))),
            ]

    monkeypatch.setattr(web_app, "pypdf", SimpleNamespace(PdfReader=Reader))
    assert web_app._extract_pdf(b"pdf") == "Readable document text"

    class EncryptedReader:
        def __init__(self, _stream):
            self.is_encrypted = True
            self.pages = []

    monkeypatch.setattr(web_app, "pypdf", SimpleNamespace(PdfReader=EncryptedReader))
    with pytest.raises(web_app.HTTPException) as encrypted:
        web_app._extract_pdf(b"pdf")
    assert encrypted.value.status_code == 400

    monkeypatch.setattr(web_app, "pypdf", None)
    with pytest.raises(web_app.HTTPException) as unavailable:
        web_app._extract_pdf(b"pdf")
    assert unavailable.value.status_code == 501
