"""In-process API smoke test; no separately running server is required."""

from fastapi.testclient import TestClient

from apps.web.app import app


def test_api_translation_connection():
    with TestClient(app) as client:
        response = client.post(
            "/translate",
            json={
                "text": "The quick brown fox jumps over the lazy dog.",
                "mirror_rate": 0.3,
                "engine": "core",
            },
        )

    assert response.status_code == 200
    assert response.json()["rows"][0]["target"]
