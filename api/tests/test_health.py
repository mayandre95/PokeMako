from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from database import get_db
from main import app
from security import verify_api_key

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_health():
    mock_session = MagicMock()
    mock_session.query.return_value.count.return_value = 42

    app.dependency_overrides[verify_api_key] = lambda: "test-key"
    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        response = client.get("/db-health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["pokemon_count"], int)
