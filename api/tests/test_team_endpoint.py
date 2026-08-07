from unittest.mock import MagicMock, patch

from database import get_db
from fastapi.testclient import TestClient
from main import app
from models import Pokemon, PokemonScore, Type

client = TestClient(app)


def _make_pokemon(pid, gen=1):
    p = MagicMock(spec=Pokemon)
    p.id = pid
    p.name_fr, p.name_en = f"Nom{pid}", f"Name{pid}"
    p.sprite_url = None
    p.generation = gen
    p.types = [MagicMock(type_id=1, type=MagicMock(name="normal"))]
    return p


def _make_db(team_pokemons, candidates=None, types=None, scores=None):
    db = MagicMock()

    def query_side_effect(model):
        q = MagicMock()
        if model is Pokemon:
            # 1er appel : équipe (filter id.in_) — 2e appel : candidats (filter ~id.in_)
            q.options.return_value.filter.return_value.all.side_effect = [
                team_pokemons,
                candidates or [],
            ]
        elif model is Type:
            q.all.return_value = types or []
        elif model is PokemonScore:
            q.all.return_value = scores or []
        return q

    db.query.side_effect = query_side_effect
    return db


def test_analyze_team_pokemon_not_found():
    app.dependency_overrides[get_db] = lambda: _make_db([])
    try:
        with patch("routers.team.get_cached", return_value=None):
            resp = client.post("/team/analyze", json={"pokemon_ids": [99999]})
    finally:
        app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_analyze_team_empty_ids_is_422():
    resp = client.post("/team/analyze", json={"pokemon_ids": []})
    assert resp.status_code == 422


def test_analyze_team_more_than_six_ids_is_422():
    resp = client.post("/team/analyze", json={"pokemon_ids": [1, 2, 3, 4, 5, 6, 7]})
    assert resp.status_code == 422


def test_analyze_team_from_cache():
    cached = {
        "team": [],
        "generation_used": 1,
        "weaknesses": [],
        "offensive_coverage": {},
        "suggestions": [],
    }
    with patch("routers.team.get_cached", return_value=cached):
        resp = client.post("/team/analyze", json={"pokemon_ids": [1]})
    assert resp.status_code == 200
    assert resp.json() == cached


def test_analyze_team_defaults_generation_to_max_of_members():
    p1, p4 = _make_pokemon(1, gen=1), _make_pokemon(4, gen=3)
    t1 = MagicMock(id=1, name="normal")

    app.dependency_overrides[get_db] = lambda: _make_db([p1, p4], types=[t1])
    try:
        with (
            patch("routers.team.get_cached", return_value=None),
            patch("routers.team.set_cache"),
            patch("routers.team._load_type_chart", return_value={}),
        ):
            resp = client.post("/team/analyze", json={"pokemon_ids": [1, 4]})
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["generation_used"] == 3


def test_analyze_team_explicit_generation_overrides_default():
    p1 = _make_pokemon(1, gen=1)
    t1 = MagicMock(id=1, name="normal")

    app.dependency_overrides[get_db] = lambda: _make_db([p1], types=[t1])
    try:
        with (
            patch("routers.team.get_cached", return_value=None),
            patch("routers.team.set_cache"),
            patch("routers.team._load_type_chart", return_value={}),
        ):
            resp = client.post(
                "/team/analyze", json={"pokemon_ids": [1], "generation": 6}
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.json()["generation_used"] == 6


def test_analyze_team_returns_min_generation():
    p1, p4 = _make_pokemon(1, gen=1), _make_pokemon(4, gen=3)
    t1 = MagicMock(id=1, name="normal")

    app.dependency_overrides[get_db] = lambda: _make_db([p1, p4], types=[t1])
    try:
        with (
            patch("routers.team.get_cached", return_value=None),
            patch("routers.team.set_cache"),
            patch("routers.team._load_type_chart", return_value={}),
        ):
            resp = client.post("/team/analyze", json={"pokemon_ids": [1, 4]})
    finally:
        app.dependency_overrides.clear()

    assert resp.json()["min_generation"] == 3


def test_analyze_team_generation_below_minimum_is_400():
    """Un Pokémon Gen 5 dans l'équipe interdit de choisir une génération < 5 —
    il n'existait pas encore."""
    p1 = _make_pokemon(1, gen=5)

    app.dependency_overrides[get_db] = lambda: _make_db([p1])
    try:
        with patch("routers.team.get_cached", return_value=None):
            resp = client.post(
                "/team/analyze", json={"pokemon_ids": [1], "generation": 2}
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 400


def test_analyze_team_returns_per_member_weaknesses_and_resistances(db_session):
    """Léviator (Eau/Vol) + Grolem (Roche/Sol) : Électrik doit apparaître dans
    les faiblesses de Léviator, et dans les résistances de Grolem."""
    from models import Pokemon, PokemonType, Type

    water = Type(name="water-test")
    ground = Type(name="ground-test")
    electric = Type(name="electric-test")
    db_session.add_all([water, ground, electric])
    db_session.flush()

    leviator = Pokemon(id=999905, name_en="gyarados", name_fr="Léviator", generation=1)
    grolem = Pokemon(id=999906, name_en="golem", name_fr="Grolem", generation=1)
    db_session.add_all([leviator, grolem])
    db_session.flush()
    db_session.add_all(
        [
            PokemonType(pokemon_id=999905, type_id=water.id, slot=1),
            PokemonType(pokemon_id=999906, type_id=ground.id, slot=1),
        ]
    )
    db_session.commit()

    chart = {(electric.id, water.id): 2.0, (electric.id, ground.id): 0.0}

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with (
            patch("routers.team.get_cached", return_value=None),
            patch("routers.team.set_cache"),
            patch("routers.team._load_type_chart", return_value=chart),
        ):
            resp = client.post("/team/analyze", json={"pokemon_ids": [999905, 999906]})
    finally:
        app.dependency_overrides.clear()

    team_by_id = {m["id"]: m for m in resp.json()["team"]}
    assert "electric-test" in team_by_id[999905]["weaknesses"]
    assert "electric-test" in team_by_id[999906]["resistances"]
    # Grolem est immunisé → la faiblesse Électrik ne doit plus apparaître
    # dans les faiblesses restantes de l'équipe, seulement dans les cumulées.
    remaining_types = [w["type"] for w in resp.json()["remaining_weaknesses"]]
    cumulative_types = [w["type"] for w in resp.json()["weaknesses"]]
    assert "electric-test" in cumulative_types
    assert "electric-test" not in remaining_types


def test_analyze_team_filters_candidates_by_generation(db_session):
    """Un candidat introduit après la génération choisie ne doit jamais être
    proposé comme suggestion — c'est le bug initialement signalé."""
    from models import Pokemon, PokemonType, Type

    type_ = Type(name="test-gen-filter-type")
    db_session.add(type_)
    db_session.flush()

    team_mon = Pokemon(id=999901, name_en="team-mon", name_fr="Equipe", generation=3)
    old_candidate = Pokemon(
        id=999902, name_en="old-mon", name_fr="Ancien", generation=2
    )
    new_candidate = Pokemon(
        id=999903, name_en="new-mon", name_fr="Nouveau", generation=5
    )
    db_session.add_all([team_mon, old_candidate, new_candidate])
    db_session.flush()
    db_session.add_all(
        [
            PokemonType(pokemon_id=999901, type_id=type_.id, slot=1),
            PokemonType(pokemon_id=999902, type_id=type_.id, slot=1),
            PokemonType(pokemon_id=999903, type_id=type_.id, slot=1),
        ]
    )
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with (
            patch("routers.team.get_cached", return_value=None),
            patch("routers.team.set_cache"),
            patch("routers.team._load_type_chart", return_value={}),
            patch("routers.team.suggest_recruits", return_value=[]) as mock_suggest,
        ):
            client.post(
                "/team/analyze", json={"pokemon_ids": [999901], "generation": 3}
            )
    finally:
        app.dependency_overrides.clear()

    candidates = mock_suggest.call_args.args[2]
    candidate_ids = [c["id"] for c in candidates]
    assert 999902 in candidate_ids
    assert 999903 not in candidate_ids
