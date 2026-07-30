from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from database import get_db
from main import app
from models import Pokemon, PokemonScore, Type

client = TestClient(app)

_SCORE_ATTRS = {
    "power_score": 400,
    "offensive_score": 180,
    "tank_score": 175,
    "meta_score": 390.0,
}


def _make_score():
    s = MagicMock()
    for k, v in _SCORE_ATTRS.items():
        setattr(s, k, v)
    return s


def _make_pokemon(type_ids=None):
    p = MagicMock()
    p.id = 1
    p.generation = 1
    p.types = [MagicMock(type_id=tid) for tid in (type_ids or [12])]
    return p


def _make_db(score, pokemon, all_type_ids=None):
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is PokemonScore:
            q.filter_by.return_value.first.return_value = score
        elif model is Pokemon:
            q.filter_by.return_value.first.return_value = pokemon
        elif model is Type:
            q.all.return_value = [MagicMock(id=tid) for tid in (all_type_ids or [])]
        return q

    db.query.side_effect = query_side_effect
    return db


def test_get_scores_from_cache():
    """Cache Redis present → retourne les donnees sans toucher la DB."""
    cached = {**_SCORE_ATTRS, "pokemon_id": 1, "generation_used": 1}
    with patch("routers.scores.get_cached", return_value=cached):
        resp = client.get("/pokemon/1/scores")
    assert resp.status_code == 200
    assert resp.json()["power_score"] == 400


def test_get_scores_from_db_default_generation():
    """Cache absent, pas de param generation → retourne le meta_score stocke."""
    score = _make_score()
    pokemon = _make_pokemon()
    app.dependency_overrides[get_db] = lambda: _make_db(score, pokemon)
    try:
        with (
            patch("routers.scores.get_cached", return_value=None),
            patch("routers.scores.set_cache"),
        ):
            resp = client.get("/pokemon/1/scores")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["meta_score"] == 390.0
    assert data["generation_used"] == 1


def test_get_scores_not_found():
    """Score introuvable en DB → 404."""
    app.dependency_overrides[get_db] = lambda: _make_db(None, None)
    try:
        with patch("routers.scores.get_cached", return_value=None):
            resp = client.get("/pokemon/99999/scores")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_get_scores_pokemon_not_found():
    """Score trouve mais Pokemon introuvable → 404."""
    score = _make_score()
    app.dependency_overrides[get_db] = lambda: _make_db(score, None)
    try:
        with patch("routers.scores.get_cached", return_value=None):
            resp = client.get("/pokemon/1/scores")
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_get_scores_with_generation_param():
    """Param ?generation=5 → recalcule le meta_score dynamiquement."""
    score = _make_score()
    pokemon = _make_pokemon(type_ids=[10])
    # attacker 1: x2.0 (weakness), attacker 2: x0.5 (resistance), attacker 3: x0.0 (immunity)
    fake_chart = {(1, 10): 2.0, (2, 10): 0.5, (3, 10): 0.0}
    app.dependency_overrides[get_db] = lambda: _make_db(
        score, pokemon, all_type_ids=[1, 2, 3]
    )
    try:
        with (
            patch("routers.scores.get_cached", return_value=None),
            patch("routers.scores.set_cache"),
            patch("routers.scores._load_type_chart", return_value=fake_chart),
        ):
            resp = client.get("/pokemon/1/scores?generation=5")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    # power=400, immunity +10, resistance +5, weakness -10 → 400 + 5 = 405
    assert data["meta_score"] == 405.0
    assert data["generation_used"] == 5
