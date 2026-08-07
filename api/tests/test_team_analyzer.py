from team_analyzer import (
    _multiplier,
    analyze_member_matchups,
    analyze_offensive_coverage,
    analyze_remaining_weaknesses,
    analyze_weaknesses,
    suggest_recruits,
)

# Types fictifs pour les tests
WATER, ELECTRIC, GRASS, FIRE = 1, 2, 3, 4


def _member(pid, type_ids):
    return {"id": pid, "type_ids": type_ids}


def test_multiplier_multiplies_across_defender_types():
    chart = {(ELECTRIC, WATER): 2.0}
    assert _multiplier(chart, ELECTRIC, [WATER]) == 2.0


def test_multiplier_defaults_to_neutral_when_absent():
    assert _multiplier({}, ELECTRIC, [WATER]) == 1.0


def test_analyze_weaknesses_detects_shared_weakness():
    chart = {(ELECTRIC, WATER): 2.0, (GRASS, WATER): 2.0}
    team = [_member(1, [WATER]), _member(2, [WATER]), _member(3, [FIRE])]

    result = analyze_weaknesses(team, chart, [WATER, ELECTRIC, GRASS, FIRE])

    by_type = {w["type_id"]: w for w in result}
    assert by_type[ELECTRIC]["weak_count"] == 2
    assert by_type[ELECTRIC]["members"] == [1, 2]
    assert GRASS in by_type
    assert FIRE not in by_type  # aucun membre n'y est faible


def test_analyze_weaknesses_sorted_by_count_descending():
    chart = {(ELECTRIC, WATER): 2.0}
    team = [_member(1, [WATER]), _member(2, [WATER]), _member(3, [WATER])]

    result = analyze_weaknesses(team, chart, [WATER, ELECTRIC])

    assert result[0]["type_id"] == ELECTRIC
    assert result[0]["weak_count"] == 3


def test_analyze_offensive_coverage_detects_gap():
    chart = {(FIRE, GRASS): 2.0}
    team = [_member(1, [WATER])]  # aucun type Feu dans l'équipe

    result = analyze_offensive_coverage(team, chart, [GRASS, WATER])

    assert GRASS in result["gaps"]


def test_analyze_offensive_coverage_detects_stab_coverage():
    chart = {(FIRE, GRASS): 2.0}
    team = [_member(1, [FIRE])]

    result = analyze_offensive_coverage(team, chart, [GRASS])

    assert result == {"covered": [GRASS], "gaps": []}


def test_suggest_recruits_prefers_resisting_candidate():
    weaknesses = [{"type_id": ELECTRIC, "weak_count": 3, "members": [1, 2, 3]}]
    chart = {(ELECTRIC, GRASS): 0.5, (ELECTRIC, FIRE): 1.0}
    candidates = [
        {"id": 10, "type_ids": [GRASS], "power_score": 300},
        {
            "id": 11,
            "type_ids": [FIRE],
            "power_score": 500,
        },  # ne résiste pas → ignoré malgré son power_score
    ]

    result = suggest_recruits(weaknesses, [], candidates, chart)

    assert [c["id"] for c in result] == [10]
    assert result[0]["covers"] == [ELECTRIC]


def test_suggest_recruits_offensive_gap_bonus():
    chart = {(FIRE, GRASS): 2.0}
    candidates = [{"id": 20, "type_ids": [FIRE], "power_score": 100}]

    result = suggest_recruits([], [GRASS], candidates, chart)

    assert result[0]["score"] == 3  # OFFENSIVE_GAP_BONUS


def test_suggest_recruits_tie_break_by_power_score():
    weaknesses = [{"type_id": ELECTRIC, "weak_count": 1, "members": [1]}]
    chart = {(ELECTRIC, GRASS): 0.5}
    candidates = [
        {"id": 30, "type_ids": [GRASS], "power_score": 200},
        {"id": 31, "type_ids": [GRASS], "power_score": 400},
    ]

    result = suggest_recruits(weaknesses, [], candidates, chart)

    assert [c["id"] for c in result] == [31, 30]


def test_suggest_recruits_excludes_zero_score_candidates():
    candidates = [{"id": 40, "type_ids": [FIRE], "power_score": 999}]
    assert suggest_recruits([], [], candidates, {}) == []


def test_analyze_member_matchups_splits_weak_and_resist():
    chart = {(ELECTRIC, WATER): 2.0, (GRASS, FIRE): 0.5}
    team = [_member(1, [WATER]), _member(2, [FIRE])]

    result = analyze_member_matchups(team, chart, [ELECTRIC, GRASS])

    assert result[1] == {"weaknesses": [ELECTRIC], "resistances": []}
    assert result[2] == {"weaknesses": [], "resistances": [GRASS]}


def test_analyze_member_matchups_neutral_counted_as_neither():
    result = analyze_member_matchups([_member(1, [WATER])], {}, [ELECTRIC])
    assert result[1] == {"weaknesses": [], "resistances": []}


def test_analyze_remaining_weaknesses_removes_covered_by_any_member():
    """Léviator (Eau/Vol, faible Électrik) + Grolem (immunisé Électrik) :
    Électrik disparaît des faiblesses restantes de l'équipe."""
    weaknesses = [{"type_id": ELECTRIC, "weak_count": 1, "members": [1]}]
    chart = {(ELECTRIC, WATER): 4.0, (ELECTRIC, GRASS): 0.0}  # 0.0 = immunité
    team = [_member(1, [WATER]), _member(2, [GRASS])]

    result = analyze_remaining_weaknesses(team, weaknesses, chart)

    assert result == []


def test_analyze_remaining_weaknesses_keeps_uncovered():
    """Aucun membre ne résiste ni n'est immunisé → la faiblesse reste."""
    weaknesses = [{"type_id": ELECTRIC, "weak_count": 2, "members": [1, 2]}]
    chart = {(ELECTRIC, WATER): 2.0}
    team = [_member(1, [WATER]), _member(2, [WATER])]

    result = analyze_remaining_weaknesses(team, weaknesses, chart)

    assert result == weaknesses


def test_suggest_recruits_respects_limit():
    weaknesses = [{"type_id": ELECTRIC, "weak_count": 1, "members": [1]}]
    chart = {(ELECTRIC, GRASS): 0.5}
    candidates = [{"id": i, "type_ids": [GRASS], "power_score": i} for i in range(10)]

    result = suggest_recruits(weaknesses, [], candidates, chart, limit=3)

    assert len(result) == 3
