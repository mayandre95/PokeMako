import pytest
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from unittest.mock import MagicMock, patch

from main import app


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_rate_limit_pokemon_passes_under_limit(client):
    """Les 5 premières requêtes passent (limite à 30/minute)."""
    from database import get_db

    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        with (
            patch("routers.pokemon.get_cached", return_value=None),
            patch("routers.pokemon.set_cache"),
        ):
            for _ in range(5):
                r = client.get("/pokemon/1")
                assert r.status_code in (200, 404)
    finally:
        app.dependency_overrides.clear()


def test_db_health_requires_api_key(client, monkeypatch):
    """GET /db-health sans header X-API-Key → 403."""
    monkeypatch.setenv("API_KEY", "test-secret")
    r = client.get("/db-health")
    assert r.status_code == 403


def test_db_health_with_valid_api_key(monkeypatch):
    """GET /db-health avec la bonne clé → 200."""
    from database import get_db

    monkeypatch.setenv("API_KEY", "test-secret")

    mock_session = MagicMock()
    mock_session.query.return_value.count.return_value = 10

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        c = TestClient(app, raise_server_exceptions=False)
        r = c.get("/db-health", headers={"X-API-Key": "test-secret"})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_db_health_with_wrong_api_key(client, monkeypatch):
    """GET /db-health avec une mauvaise clé → 403."""
    monkeypatch.setenv("API_KEY", "test-secret")
    r = client.get("/db-health", headers={"X-API-Key": "wrong-key"})
    assert r.status_code == 403


def test_db_health_api_key_not_configured(client, monkeypatch):
    """GET /db-health quand API_KEY n'est pas définie côté serveur → 500."""
    monkeypatch.delenv("API_KEY", raising=False)
    r = client.get("/db-health", headers={"X-API-Key": "any-key"})
    assert r.status_code == 500


def test_rate_limit_handler_registered():
    """Le handler RateLimitExceeded est enregistré dans l'app."""
    assert RateLimitExceeded in app.exception_handlers
