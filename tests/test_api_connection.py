"""In-process API smoke test; no separately running server is required."""

from fastapi.testclient import TestClient

import apps.web.app as web_app
from apps.web.app import SlidingWindowRateLimiter, app


def test_api_translation_connection(monkeypatch):
    monkeypatch.setattr(web_app, "API_KEY", "test-api-key")
    monkeypatch.setattr(web_app, "rate_limiter", SlidingWindowRateLimiter(1000))
    with TestClient(app) as client:
        response = client.post(
            "/translate",
            headers={"X-API-Key": "test-api-key"},
            json={
                "text": "The quick brown fox jumps over the lazy dog.",
                "mirror_rate": 0.3,
                "engine": "core",
            },
        )

    assert response.status_code == 200
    assert response.json()["rows"][0]["target"]
