from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from database import get_db
from main import app

client = TestClient(app)

_POKEMON_ATTRS = {
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


def _make_pokemon():
    m = MagicMock()
    for k, v in _POKEMON_ATTRS.items():
        setattr(m, k, v)
    return m


def _make_db(pokemon=None):
    s = MagicMock()
    s.query.return_value.options.return_value.filter.return_value.first.return_value = (
        pokemon
    )
    return s


def test_get_pokemon_from_db():
    """Premier appel : récupère depuis PostgreSQL et met en cache."""
    app.dependency_overrides[get_db] = lambda: _make_db(_make_pokemon())
    try:
        with (
            patch("routers.pokemon.get_cached", return_value=None),
            patch("routers.pokemon.set_cache"),
        ):
            response = client.get("/pokemon/1")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name_en"] == "Bulbasaur"
    assert data["name_fr"] == "Bulbizarre"


def test_get_pokemon_from_cache():
    """Deuxième appel : doit venir du cache Redis sans toucher la DB."""
    with patch("routers.pokemon.get_cached", return_value=_POKEMON_ATTRS):
        response = client.get("/pokemon/1")
    assert response.status_code == 200


def test_get_pokemon_not_found():
    """Pokémon inexistant → 404."""
    app.dependency_overrides[get_db] = lambda: _make_db(None)
    try:
        with patch("routers.pokemon.get_cached", return_value=None):
            response = client.get("/pokemon/99999")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 404
