from unittest.mock import MagicMock, patch

import httpx
from fastapi.testclient import TestClient
from main import app
from routers.pokemon import _area_name_fr

client = TestClient(app)

_SAMPLE_ENCOUNTERS = [
    {
        "location_area": {"name": "viridian-forest-area"},
        "version_details": [
            {
                "version": {"name": "red"},
                "encounter_details": [
                    {
                        "method": {"name": "walk"},
                        "chance": 25,
                        "min_level": 3,
                        "max_level": 5,
                        "condition_values": [],
                    }
                ],
            }
        ],
    }
]


def _http_resp(status=200, data=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data if data is not None else []
    r.raise_for_status = MagicMock()
    return r


def _mock_httpx(encounters_resp, area_resp=None):
    """Retourne une classe httpx.Client mockée utilisable comme context manager."""
    mock_instance = MagicMock()

    def _get(url, **kw):
        if "location-area" in url:
            return area_resp or _http_resp(200, {"names": []})
        return encounters_resp

    mock_instance.get.side_effect = _get
    mock_instance.__enter__ = lambda s: mock_instance
    mock_instance.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_instance)


# ── _area_name_fr ──────────────────────────────────────────────────────────


def test_area_name_fr_cache_hit():
    """Cache Redis présent → retourne directement le nom sans appel HTTP."""
    with patch("routers.pokemon.get_cached", return_value={"name": "Forêt de Jade"}):
        result = _area_name_fr(MagicMock(), "viridian-forest-area")
    assert result == "Forêt de Jade"


def test_area_name_fr_found():
    """PokéAPI retourne un nom FR → le retourne et le met en cache."""
    area_data = {
        "names": [
            {"language": {"name": "en"}, "name": "Viridian Forest"},
            {"language": {"name": "fr"}, "name": "Forêt de Jade"},
        ]
    }
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, area_data)
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache") as mock_set,
    ):
        result = _area_name_fr(mock_client, "viridian-forest-area")
    assert result == "Forêt de Jade"
    mock_set.assert_called_once()


def test_area_name_fr_no_french():
    """PokéAPI ne contient pas de nom FR → retourne None et met None en cache."""
    area_data = {"names": [{"language": {"name": "en"}, "name": "Viridian Forest"}]}
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, area_data)
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache") as mock_set,
    ):
        result = _area_name_fr(mock_client, "viridian-forest-area")
    assert result is None
    mock_set.assert_called_once()


def test_area_name_fr_api_error():
    """PokéAPI retourne non-200 → retourne None sans mettre en cache."""
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(404)
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache") as mock_set,
    ):
        result = _area_name_fr(mock_client, "unknown-area")
    assert result is None
    mock_set.assert_not_called()


# ── GET /pokemon/{id}/encounters ───────────────────────────────────────────


def test_get_encounters_from_cache():
    """Cache Redis présent → retourne les données sans appel HTTP."""
    cached = {"encounters": [], "has_encounters": False}
    with patch("routers.pokemon.get_cached", return_value=cached):
        resp = client.get("/pokemon/25/encounters")
    assert resp.status_code == 200
    assert resp.json()["has_encounters"] is False


def test_get_encounters_from_api():
    """Cache absent, PokéAPI OK avec nom FR → retourne les encounters avec location_area_fr."""
    area_data = {"names": [{"language": {"name": "fr"}, "name": "Forêt de Jade"}]}
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch(
            "routers.pokemon.httpx.Client",
            _mock_httpx(
                _http_resp(200, _SAMPLE_ENCOUNTERS), _http_resp(200, area_data)
            ),
        ),
    ):
        resp = client.get("/pokemon/25/encounters")

    assert resp.status_code == 200
    data = resp.json()
    assert data["has_encounters"] is True
    enc = data["encounters"][0]
    assert enc["game"] == "red"
    assert enc["method"] == "walk"
    assert enc["min_level"] == 3
    assert enc["max_level"] == 5
    assert enc["location_area_fr"] == "Forêt de Jade"


def test_get_encounters_no_fr_area_name():
    """PokéAPI ne fournit pas de nom FR pour la zone → location_area_fr absent."""
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch(
            "routers.pokemon.httpx.Client",
            _mock_httpx(
                _http_resp(200, _SAMPLE_ENCOUNTERS), _http_resp(200, {"names": []})
            ),
        ),
    ):
        resp = client.get("/pokemon/25/encounters")

    assert resp.status_code == 200
    data = resp.json()
    assert data["has_encounters"] is True
    assert "location_area_fr" not in data["encounters"][0]


def test_get_encounters_empty():
    """PokéAPI retourne une liste vide → has_encounters False."""
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch("routers.pokemon.httpx.Client", _mock_httpx(_http_resp(200, []))),
    ):
        resp = client.get("/pokemon/25/encounters")

    assert resp.status_code == 200
    assert resp.json()["has_encounters"] is False


def test_get_encounters_not_found():
    """PokéAPI retourne 404 → HTTP 404."""
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.httpx.Client", _mock_httpx(_http_resp(404))),
    ):
        resp = client.get("/pokemon/99999/encounters")

    assert resp.status_code == 404


def test_area_name_fr_read_timeout():
    """ReadTimeout lors de l'appel PokéAPI → retourne None sans mettre en cache."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ReadTimeout("timeout")
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache") as mock_set,
    ):
        result = _area_name_fr(mock_client, "some-area")
    assert result is None
    mock_set.assert_not_called()


def test_area_name_fr_connect_timeout():
    """ConnectTimeout lors de l'appel PokéAPI → retourne None sans mettre en cache."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectTimeout("timeout")
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.set_cache") as mock_set,
    ):
        result = _area_name_fr(mock_client, "some-area")
    assert result is None
    mock_set.assert_not_called()
