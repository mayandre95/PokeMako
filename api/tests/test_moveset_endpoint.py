from unittest.mock import MagicMock, patch

from database import get_db
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

_SAMPLE_MOVE = {
    "id": 94,
    "name_fr": "Psyko",
    "name_en": "Psychic",
    "type": "psychic",
    "damage_class": "special",
    "power": 90,
    "accuracy": 100,
    "pp": 10,
    "method": "level-up",
    "level_learned": 1,
    "version_group": "scarlet-violet",
}


def _make_db(pokemon, types=None):
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = pokemon
    db.query.return_value.all.return_value = types or []
    return db


def _mock_client():
    mock_instance = MagicMock()
    mock_instance.__enter__ = lambda s: mock_instance
    mock_instance.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_instance)


def test_recommend_moveset_pokemon_not_found():
    app.dependency_overrides[get_db] = lambda: _make_db(None)
    try:
        resp = client.post(
            "/pokemon/99999/recommend-moveset",
            json={"role": "attacker", "version_group": "scarlet-violet"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_recommend_moveset_invalid_role():
    pokemon = MagicMock(id=65, generation=1, attack=50, sp_attack=135)
    app.dependency_overrides[get_db] = lambda: _make_db(pokemon)
    try:
        resp = client.post(
            "/pokemon/65/recommend-moveset",
            json={"role": "invalide", "version_group": "scarlet-violet"},
        )
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_recommend_moveset_missing_version_group_is_422():
    pokemon = MagicMock(id=65, generation=1, attack=50, sp_attack=135)
    app.dependency_overrides[get_db] = lambda: _make_db(pokemon)
    try:
        resp = client.post("/pokemon/65/recommend-moveset", json={"role": "attacker"})
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_recommend_moveset_returns_moves_for_requested_version():
    pokemon = MagicMock(id=65, generation=1, attack=50, sp_attack=135)
    with (
        patch("routers.moveset._build_movepool", return_value=[_SAMPLE_MOVE]),
        patch("moveset_optimizer._load_type_chart", return_value={}),
        patch("routers.moveset.httpx.Client", _mock_client()),
    ):
        app.dependency_overrides[get_db] = lambda: _make_db(
            pokemon, [MagicMock(id=1, name="psychic")]
        )
        try:
            resp = client.post(
                "/pokemon/65/recommend-moveset",
                json={"role": "attacker", "version_group": "scarlet-violet"},
            )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "attacker"
    assert data["version_group"] == "scarlet-violet"
    assert data["moves"][0]["name_fr"] == "Psyko"
    assert data["moves"][0]["method_label"] is None  # level-up
    assert "reason" in data["moves"][0]


def test_recommend_moveset_exclude_hm_true_is_accepted():
    pokemon = MagicMock(id=65, generation=1, attack=50, sp_attack=135)
    with (
        patch("routers.moveset._build_movepool", return_value=[_SAMPLE_MOVE]),
        patch("moveset_optimizer._load_type_chart", return_value={}),
        patch("routers.moveset.httpx.Client", _mock_client()),
    ):
        app.dependency_overrides[get_db] = lambda: _make_db(
            pokemon, [MagicMock(id=1, name="psychic")]
        )
        try:
            resp = client.post(
                "/pokemon/65/recommend-moveset",
                json={
                    "role": "attacker",
                    "version_group": "scarlet-violet",
                    "exclude_hm": True,
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200


def test_recommend_moveset_exclude_tm_true_is_accepted():
    pokemon = MagicMock(id=65, generation=1, attack=50, sp_attack=135)
    with (
        patch("routers.moveset._build_movepool", return_value=[_SAMPLE_MOVE]),
        patch("moveset_optimizer._load_type_chart", return_value={}),
        patch("routers.moveset.httpx.Client", _mock_client()),
    ):
        app.dependency_overrides[get_db] = lambda: _make_db(
            pokemon, [MagicMock(id=1, name="psychic")]
        )
        try:
            resp = client.post(
                "/pokemon/65/recommend-moveset",
                json={
                    "role": "attacker",
                    "version_group": "scarlet-violet",
                    "exclude_tm": True,
                },
            )
        finally:
            app.dependency_overrides.clear()

    assert resp.status_code == 200
