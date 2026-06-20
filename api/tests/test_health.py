from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from database import get_db
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_db_health():
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0

    app.dependency_overrides[get_db] = lambda: mock_db
    response = client.get("/db-health")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "pokemon_count" in data
