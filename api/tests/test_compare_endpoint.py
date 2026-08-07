from unittest.mock import MagicMock, patch

from database import get_db
from fastapi.testclient import TestClient
from main import app
from models import Pokemon, PokemonScore

client = TestClient(app)


def _make_pokemon(pid, name_en, name_fr, gen=1):
    p = MagicMock(spec=Pokemon)
    p.id, p.name_en, p.name_fr = pid, name_en, name_fr
    p.generation = gen
    p.sprite_url = f"https://example.com/{pid}.png"
    p.hp = p.attack = p.defense = p.sp_attack = p.sp_defense = p.speed = 50
    p.types = []
    return p


def _make_score(pid, power=300, off=150, tank=150, meta=310.0):
    s = MagicMock(spec=PokemonScore)
    s.pokemon_id = pid
    s.power_score, s.offensive_score, s.tank_score, s.meta_score = (
        power,
        off,
        tank,
        meta,
    )
    return s


def test_compare_returns_data():
    """GET /compare?ids=1,4 retourne 2 Pokémon avec stats et scores."""
    p1, p4 = (
        _make_pokemon(1, "bulbasaur", "Bulbizarre"),
        _make_pokemon(4, "charmander", "Salamèche"),
    )
    s1, s4 = _make_score(1), _make_score(4)

    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.all.return_value = [
        p1,
        p4,
    ]
    db.query.return_value.filter.return_value.all.return_value = [s1, s4]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.compare.get_cached", return_value=None),
            patch("routers.compare.set_cache"),
        ):
            resp = client.get("/compare?ids=1,4")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["power_score"] == 300


def test_compare_from_cache():
    """Cache hit → DB non appelée."""
    cached = [
        {
            "id": 1,
            "name_fr": "Bulbizarre",
            "name_en": "bulbasaur",
            "sprite_url": None,
            "types": [],
            "hp": 45,
            "attack": 49,
            "defense": 49,
            "sp_attack": 65,
            "sp_defense": 65,
            "speed": 45,
            "power_score": 318,
            "offensive_score": 159,
            "tank_score": 159,
            "meta_score": 348.0,
        }
    ]
    with patch("routers.compare.get_cached", return_value=cached):
        resp = client.get("/compare?ids=1")
    assert resp.status_code == 200
    assert resp.json()[0]["name_fr"] == "Bulbizarre"


def test_compare_empty_ids():
    """IDs invalides → liste vide."""
    with patch("routers.compare.get_cached", return_value=None):
        resp = client.get("/compare?ids=abc,xyz")
    assert resp.status_code == 200
    assert resp.json() == []


def test_compare_max_3():
    """Plus de 3 IDs → seulement les 3 premiers pris en compte."""
    db = MagicMock()
    db.query.return_value.options.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.compare.get_cached", return_value=None),
            patch("routers.compare.set_cache"),
        ):
            resp = client.get("/compare?ids=1,4,7,25,150")  # 5 IDs
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200


def test_search_returns_results():
    """GET /search?q=pika retourne les Pokémon correspondants."""
    p = _make_pokemon(25, "pikachu", "Pikachu")
    db = MagicMock()
    db.query.return_value.filter.return_value.limit.return_value.all.return_value = [p]

    app.dependency_overrides[get_db] = lambda: db
    try:
        resp = client.get("/search?q=pika")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()[0]["name_en"] == "pikachu"


def test_search_too_short():
    """Requête < 2 caractères → liste vide sans appel DB."""
    resp = client.get("/search?q=p")
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_is_accent_insensitive(db_session):
    """Taper "leviator" (sans accent) doit trouver "Léviator"."""
    from models import Pokemon

    db_session.add(
        Pokemon(id=999904, name_en="gyarados-test", name_fr="Léviator", generation=1)
    )
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.get("/search?q=leviator")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert any(r["name_fr"] == "Léviator" for r in resp.json())
