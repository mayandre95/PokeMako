import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring import (
    _load_type_chart,
    compute_offensive_score,
    compute_power_score,
    compute_tank_score,
)


def _make_pokemon(hp=45, atk=49, def_=49, spatk=65, spdef=65, speed=45):
    p = MagicMock()
    p.hp, p.attack, p.defense = hp, atk, def_
    p.sp_attack, p.sp_defense, p.speed = spatk, spdef, speed
    return p


def test_power_score_bulbasaur():
    assert compute_power_score(_make_pokemon()) == 318


def test_power_score_ignores_none():
    assert compute_power_score(_make_pokemon(atk=None)) == 269


def test_offensive_score():
    assert compute_offensive_score(_make_pokemon(atk=49, spatk=65, speed=45)) == 159


def test_offensive_score_none_treated_as_zero():
    assert compute_offensive_score(_make_pokemon(atk=None, spatk=65, speed=45)) == 110


def test_tank_score():
    assert compute_tank_score(_make_pokemon(hp=45, def_=49, spdef=65)) == 159


def test_load_type_chart_queries_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.group_by.return_value.subquery.return_value = MagicMock()
    db.query.return_value.join.return_value.all.return_value = []
    result = _load_type_chart(db, generation=1)
    assert isinstance(result, dict)
    db.query.assert_called()


def test_meta_score_generation_aware():
    from scoring import compute_meta_score

    db = MagicMock()
    db.query.return_value.all.return_value = []
    with patch("scoring._load_type_chart", return_value={}) as mock_load:
        compute_meta_score(db, power=400, pokemon_type_ids=[1], generation=5)
    mock_load.assert_called_once_with(db, 5)


def test_compute_meta_score_counts_bonuses():
    """Exercice du corps de la boucle : immunité +10, résistance +5, faiblesse −10."""
    from scoring import compute_meta_score

    db = MagicMock()
    t1, t2, t3 = MagicMock(), MagicMock(), MagicMock()
    t1.id, t2.id, t3.id = 1, 2, 3
    db.query.return_value.all.return_value = [t1, t2, t3]

    # attaquant 1 → ×2.0 (faiblesse), 2 → ×0.5 (résistance), 3 → ×0.0 (immunité)
    fake_chart = {(1, 10): 2.0, (2, 10): 0.5, (3, 10): 0.0}

    with patch("scoring._load_type_chart", return_value=fake_chart):
        result = compute_meta_score(db, power=300, pokemon_type_ids=[10], generation=1)

    # 300 + 1×10 + 1×5 − 1×10 = 305
    assert result == 305.0


def test_compute_meta_score_dual_type_multiplies():
    """Type double : multiplicateurs cumulés → faiblesse ×4 comptée comme une seule."""
    from scoring import compute_meta_score

    db = MagicMock()
    t = MagicMock()
    t.id = 1
    db.query.return_value.all.return_value = [t]

    # attaquant 1 fait ×2 contre type 10 et ×2 contre type 11 → mult total ×4 (faiblesse)
    fake_chart = {(1, 10): 2.0, (1, 11): 2.0}

    with patch("scoring._load_type_chart", return_value=fake_chart):
        result = compute_meta_score(
            db, power=100, pokemon_type_ids=[10, 11], generation=1
        )

    # 100 − 1×10 = 90
    assert result == 90.0


def _make_role_pokemon(hp, atk, def_, spatk, spdef, speed):
    p = MagicMock()
    p.hp, p.attack, p.defense = hp, atk, def_
    p.sp_attack, p.sp_defense, p.speed = spatk, spdef, speed
    return p


def test_role_scores_blissey_is_tank_dominant():
    """Blissey (255/10/10/75/135/55) : Tank domine, Support est 2e — cas d'acceptation du ticket."""
    from scoring import compute_dominant_role, compute_role_scores

    blissey = _make_role_pokemon(hp=255, atk=10, def_=10, spatk=75, spdef=135, speed=55)
    scores = compute_role_scores(blissey)

    assert compute_dominant_role(scores) == "tank_role_score"
    ranked = sorted(scores, key=scores.get, reverse=True)
    assert ranked[1] == "support_score"


def test_role_scores_alakazam_is_sweeper_dominant():
    """Alakazam (55/50/45/135/95/120) : Sweeper domine — cas d'acceptation du ticket."""
    from scoring import compute_dominant_role, compute_role_scores

    alakazam = _make_role_pokemon(
        hp=55, atk=50, def_=45, spatk=135, spdef=95, speed=120
    )
    scores = compute_role_scores(alakazam)

    assert compute_dominant_role(scores) == "sweeper_score"


def test_versatility_never_exceeds_max_base_role():
    """Propriété mathématique : une moyenne ne dépasse jamais le max de son échantillon."""
    from scoring import compute_role_scores

    mon = _make_role_pokemon(hp=100, atk=100, def_=100, spatk=100, spdef=100, speed=100)
    scores = compute_role_scores(mon)
    base = [
        scores["attacker_score"],
        scores["tank_role_score"],
        scores["support_score"],
        scores["sweeper_score"],
    ]
    assert scores["versatility_score"] <= max(base)
