from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_pokemon_from_db():
    """Premier appel : récupère depuis PostgreSQL et met en cache."""
    with patch("routers.pokemon.get_cached", return_value=None):
        with patch("routers.pokemon.set_cache"):
            response = client.get("/pokemon/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name_en"] == "Bulbasaur"
    assert data["name_fr"] == "Bulbizarre"


def test_get_pokemon_from_cache():
    """Deuxième appel : doit venir du cache Redis."""
    cached_data = {
        "id": 1,
        "name": "Bulbizarre",
        "name_en": "Bulbasaur",
        "name_fr": "Bulbizarre",
        "generation": 1,
        "hp": 45,
        "attack": 49,
        "defense": 49,
        "sp_attack": 65,
        "sp_defense": 65,
        "speed": 45,
        "base_experience": 64,
        "height": 7,
        "weight": 69,
        "is_legendary": False,
        "is_mythical": False,
        "sprite_url": None,
        "artwork_url": None,
    }
    with patch("routers.pokemon.get_cached", return_value=cached_data):
        response = client.get("/pokemon/1")
    assert response.status_code == 200


def test_get_pokemon_not_found():
    with patch("routers.pokemon.get_cached", return_value=None):
        response = client.get("/pokemon/99999")
    assert response.status_code == 404
