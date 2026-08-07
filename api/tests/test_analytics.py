from unittest.mock import MagicMock, patch

from database import get_db
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_types_from_cache():
    """Cache hit → DB non appelée."""
    cached = [{"type": "water", "count": 133}]
    with patch("routers.analytics.get_cached", return_value=cached):
        resp = client.get("/analytics/types")
    assert resp.status_code == 200
    assert resp.json()[0]["type"] == "water"


def test_types_from_db():
    """Mock 2 types en DB → réponse JSON triée par count desc."""
    db = MagicMock()
    # simulate .query(Type.name, func.count(...)).join(...).group_by(...).order_by(...).all()
    row1, row2 = MagicMock(), MagicMock()
    row1.name, row1.count = "water", 133
    row2.name, row2.count = "fire", 64
    db.query.return_value.join.return_value.group_by.return_value.order_by.return_value.all.return_value = [
        row1,
        row2,
    ]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.analytics.get_cached", return_value=None),
            patch("routers.analytics.set_cache"),
        ):
            resp = client.get("/analytics/types")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data[0] == {"type": "water", "count": 133}
    assert data[1] == {"type": "fire", "count": 64}


def test_type_chart_from_cache():
    """Cache hit → DB non appelée."""
    cached = {"generation": 9, "types": ["fire"], "matrix": {"fire": {"fire": 0.5}}}
    with patch("routers.analytics.get_cached", return_value=cached):
        resp = client.get("/analytics/type-chart")
    assert resp.status_code == 200
    assert resp.json() == cached


def test_type_chart_builds_full_matrix():
    """2 types en DB → matrice 2×2 avec les multiplicateurs du chart."""
    # .name ne peut pas être passé au constructeur MagicMock() : c'est un
    # paramètre spécial (nom interne du mock pour son repr), pas un moyen de
    # définir l'attribut .name — il faut l'assigner après coup.
    fire, grass = MagicMock(), MagicMock()
    fire.id, fire.name = 1, "fire"
    grass.id, grass.name = 2, "grass"
    db = MagicMock()
    db.query.return_value.order_by.return_value.all.return_value = [fire, grass]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.analytics.get_cached", return_value=None),
            patch("routers.analytics.set_cache"),
            patch("routers.analytics._load_type_chart", return_value={(1, 2): 2.0}),
        ):
            resp = client.get("/analytics/type-chart?generation=9")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["generation"] == 9
    assert data["types"] == ["fire", "grass"]
    assert data["matrix"]["fire"]["grass"] == 2.0
    assert data["matrix"]["fire"]["fire"] == 1.0  # absent du chart → neutre


def test_generations_from_cache():
    """Cache hit → DB non appelée."""
    cached = [
        {
            "generation": 1,
            "hp": 45.0,
            "attack": 49.0,
            "defense": 49.0,
            "sp_attack": 65.0,
            "sp_defense": 65.0,
            "speed": 45.0,
        }
    ]
    with patch("routers.analytics.get_cached", return_value=cached):
        resp = client.get("/analytics/generations")
    assert resp.status_code == 200
    assert resp.json()[0]["generation"] == 1


def test_generations_from_db():
    """2 Pokémon sur 2 générations → moyennes correctes via pandas."""
    db = MagicMock()
    p1, p2 = MagicMock(), MagicMock()
    p1.generation, p1.hp, p1.attack, p1.defense = 1, 45, 49, 49
    p1.sp_attack, p1.sp_defense, p1.speed = 65, 65, 45
    p2.generation, p2.hp, p2.attack, p2.defense = 2, 55, 60, 50
    p2.sp_attack, p2.sp_defense, p2.speed = 70, 70, 55
    # Le code appelle db.query(Pokemon).all() — sans .filter()
    db.query.return_value.all.return_value = [p1, p2]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.analytics.get_cached", return_value=None),
            patch("routers.analytics.set_cache"),
        ):
            resp = client.get("/analytics/generations")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["generation"] == 1
    assert data[0]["hp"] == 45.0


def test_generations_empty_db():
    """Aucun Pokémon en DB → liste vide."""
    db = MagicMock()
    db.query.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.analytics.get_cached", return_value=None),
            patch("routers.analytics.set_cache"),
        ):
            resp = client.get("/analytics/generations")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


def test_scatter_from_cache():
    """Cache hit -> DB not called."""
    cached = [
        {"name": "Pikachu", "speed": 90, "power_score": 320, "primary_type": "electric"}
    ]
    with patch("routers.analytics.get_cached", return_value=cached):
        resp = client.get("/analytics/scatter")
    assert resp.status_code == 200
    assert resp.json()[0]["name"] == "Pikachu"


def test_scatter_from_db():
    """Mock Pokémon + PokemonScore + Type → champs présents dans la réponse."""
    db = MagicMock()
    row = MagicMock()
    row.Pokemon.name_fr, row.Pokemon.name_en = "Pikachu", "Pikachu"
    row.Pokemon.speed = 90
    row.PokemonScore.power_score = 320
    row.primary_type = "electric"
    db.query.return_value.join.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value.all.return_value = [
        row
    ]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.analytics.get_cached", return_value=None),
            patch("routers.analytics.set_cache"),
        ):
            resp = client.get("/analytics/scatter")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    point = resp.json()[0]
    assert point["name"] == "Pikachu"
    assert point["speed"] == 90
    assert point["power_score"] == 320
    assert point["primary_type"] == "electric"
