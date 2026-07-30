import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "etl"))

import compute_scores


def _make_pokemon(pid=1, gen=1, hp=45, atk=49, def_=49, spatk=65, spdef=65, speed=45):
    p = MagicMock()
    p.id = pid
    p.generation = gen
    p.hp, p.attack, p.defense = hp, atk, def_
    p.sp_attack, p.sp_defense, p.speed = spatk, spdef, speed
    p.types = [MagicMock(type_id=1)]
    return p


def _make_db(pokemons):
    db = MagicMock()
    db.query.return_value.all.return_value = pokemons
    db.__enter__ = lambda s: db
    db.__exit__ = MagicMock(return_value=False)
    return db


def test_run_executes_upsert_and_commits():
    """run() calcule les scores, execute un upsert par Pokemon et commite."""
    poke = _make_pokemon()
    db = _make_db([poke])

    with (
        patch("compute_scores.SessionLocal", return_value=db),
        patch("compute_scores._load_type_chart", return_value={}),
    ):
        compute_scores.run()

    db.execute.assert_called_once()
    db.commit.assert_called_once()


def test_run_covers_all_multiplier_branches():
    """Lines 41/43/45: immunity/resistance/weakness branches in the scoring loop."""
    from models import Pokemon, Type as TypeModel

    poke = _make_pokemon()
    t1, t2, t3 = MagicMock(), MagicMock(), MagicMock()
    t1.id, t2.id, t3.id = 1, 2, 3

    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Pokemon:
            q.all.return_value = [poke]
        elif model is TypeModel:
            q.all.return_value = [t1, t2, t3]
        return q

    db.query.side_effect = query_side
    db.__enter__ = lambda s: db
    db.__exit__ = MagicMock(return_value=False)

    # poke.types[0].type_id = 1 — attacker 1: immunity, 2: resistance, 3: weakness
    fake_chart = {(1, 1): 0.0, (2, 1): 0.5, (3, 1): 2.0}

    with (
        patch("compute_scores.SessionLocal", return_value=db),
        patch("compute_scores._load_type_chart", return_value=fake_chart),
    ):
        compute_scores.run()

    db.execute.assert_called_once()


def test_run_loads_chart_once_per_generation():
    """run() charge le type chart une seule fois par generation distincte."""
    poke1 = _make_pokemon(pid=1, gen=1)
    poke2 = _make_pokemon(pid=2, gen=2)
    poke3 = _make_pokemon(pid=3, gen=1)  # meme gen que poke1 → pas de rechargement
    db = _make_db([poke1, poke2, poke3])

    with (
        patch("compute_scores.SessionLocal", return_value=db),
        patch("compute_scores._load_type_chart", return_value={}) as mock_chart,
    ):
        compute_scores.run()

    # Deux generations distinctes (1 et 2) → deux appels
    assert mock_chart.call_count == 2
    db.commit.assert_called_once()
