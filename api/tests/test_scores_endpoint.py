from unittest.mock import MagicMock, patch

from database import get_db
from fastapi.testclient import TestClient
from main import app
from models import Pokemon, PokemonScore, Type

client = TestClient(app)

_SCORE_ATTRS = {
    "power_score": 400,
    "offensive_score": 180,
    "tank_score": 175,
    "meta_score": 390.0,
    "attacker_score": 120.0,
    "tank_role_score": 300.0,
    "support_score": 150.0,
    "sweeper_score": 140.0,
    "versatility_score": 100.0,
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
            patch("scoring._load_type_chart", return_value=fake_chart),
        ):
            resp = client.get("/pokemon/1/scores?generation=5")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    # power=400, immunity +10, resistance +5, weakness -10 → 400 + 5 = 405
    assert data["meta_score"] == 405.0
    assert data["generation_used"] == 5


def test_scores_history_returns_9_entries():
    """L'historique retourne exactement 9 entrées (Gen 1 à 9)."""
    db = MagicMock()

    score = MagicMock()
    score.power_score = 300

    pokemon = MagicMock()
    pokemon.generation = 4
    pokemon.types = []

    # scores query → score, pokemon query → pokemon
    db.query.return_value.filter_by.return_value.first.side_effect = [score, pokemon]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with (
            patch("routers.scores.get_cached", return_value=None),
            patch("routers.scores.set_cache"),
            patch("scoring.compute_meta_score", return_value=300.0),
        ):
            resp = client.get("/pokemon/1/scores/history")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 9
    # Gen 1-3 inactive (Pokémon est Gen 4), Gen 4-9 active
    assert data[0]["active"] is False  # Gen 1
    assert data[3]["active"] is True  # Gen 4
    assert data[8]["active"] is True  # Gen 9


def test_scores_history_from_cache():
    """Cache hit → DB non appelée."""
    cached = [
        {"generation": g, "meta_score": 300.0, "active": g >= 1} for g in range(1, 10)
    ]
    with patch("routers.scores.get_cached", return_value=cached):
        resp = client.get("/pokemon/1/scores/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 9


def test_scores_history_not_found():
    """Score introuvable → 404."""
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: db
    try:
        with patch("routers.scores.get_cached", return_value=None):
            resp = client.get("/pokemon/99999/scores/history")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404


def test_scores_history_pokemon_not_found():
    """Score présent mais Pokémon introuvable → 404 (ligne 85)."""
    db = MagicMock()
    db.query.return_value.filter_by.return_value.first.side_effect = [
        MagicMock(power_score=300),  # score trouvé
        None,  # pokemon introuvable
    ]

    app.dependency_overrides[get_db] = lambda: db
    try:
        with patch("routers.scores.get_cached", return_value=None):
            resp = client.get("/pokemon/99999/scores/history")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404


def test_get_scores_includes_dominant_role():
    """La réponse inclut les 5 scores de rôle et le rôle dominant (tank_role_score ici, le plus élevé)."""
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

    data = resp.json()
    assert data["dominant_role"] == "tank_role_score"
    assert data["support_score"] == 150.0
