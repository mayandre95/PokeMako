import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from moveset_optimizer import (
    _dominant_damage_class,
    _has_enabler,
    _move_dps,
    _move_machines,
    _type_coverage,
    deduplicate_moves,
    filter_by_version_group,
    is_hm,
    method_label,
    recommend_moveset,
)

VG = "scarlet-violet"


def _move(
    id,
    type_="normal",
    damage_class="physical",
    power=80,
    accuracy=100,
    pp=15,
    method="level-up",
    version_group=VG,
    ailment=None,
):
    return {
        "id": id,
        "name_fr": f"Move{id}",
        "name_en": f"Move{id}",
        "type": type_,
        "damage_class": damage_class,
        "power": power,
        "accuracy": accuracy,
        "pp": pp,
        "method": method,
        "version_group": version_group,
        "level_learned": 1,
        "ailment": ailment,
    }


def _make_db(types):
    db = MagicMock()
    db.query.return_value.all.return_value = types
    return db


def _http_resp(status=200, data=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data if data is not None else {}
    return r


# ── Filtrage par version / déduplication ────────────────────────────────────


def test_filter_by_version_group():
    pool = [_move(1, version_group="red-blue"), _move(2, version_group=VG)]
    result = filter_by_version_group(pool, VG)
    assert [m["id"] for m in result] == [2]


def test_deduplicate_moves_prefers_level_up_over_machine():
    """Une attaque apprise à la fois par niveau et par CT dans la même version :
    on garde la méthode level-up (pas besoin de CT si déjà connue)."""
    pool = [_move(1, method="machine"), _move(1, method="level-up")]
    result = deduplicate_moves(pool)
    assert len(result) == 1
    assert result[0]["method"] == "level-up"


# ── DPS / couverture (inchangés) ────────────────────────────────────────────


def test_move_dps_treats_null_accuracy_as_certain():
    assert _move_dps(_move(1, power=100, accuracy=None)) == 100.0


def test_move_dps_formula():
    assert _move_dps(_move(1, power=80, accuracy=90)) == 72.0


def test_type_coverage_counts_super_effective_types():
    chart = {(1, 10): 2.0, (1, 11): 0.5, (1, 12): 1.0}
    assert _type_coverage(1, chart, [10, 11, 12]) == 1


def test_dominant_damage_class_physical():
    assert _dominant_damage_class(MagicMock(attack=100, sp_attack=50)) == "physical"


def test_dominant_damage_class_special():
    assert _dominant_damage_class(MagicMock(attack=50, sp_attack=100)) == "special"


# ── CT / CS ──────────────────────────────────────────────────────────────────


def test_is_hm_true_when_item_starts_with_hm():
    client = MagicMock()
    client.get.side_effect = [
        _http_resp(
            200,
            {
                "machines": [
                    {
                        "machine": {"url": "https://x/machine/1/"},
                        "version_group": {"name": VG},
                    }
                ]
            },
        ),
        _http_resp(200, {"item": {"name": "hm03"}}),
    ]
    with (
        patch("moveset_optimizer.get_cached", return_value=None),
        patch("moveset_optimizer.set_cache"),
    ):
        assert is_hm(client, 57, VG) is True


def test_is_hm_false_when_no_machine_for_this_version():
    client = MagicMock()
    client.get.return_value = _http_resp(200, {"machines": []})
    with (
        patch("moveset_optimizer.get_cached", return_value=None),
        patch("moveset_optimizer.set_cache"),
    ):
        assert is_hm(client, 57, VG) is False


def test_move_machines_empty_result_is_still_cached_correctly():
    """Un dict vide {} caché tel quel serait "falsy" et referait l'appel HTTP à
    chaque fois — vérifie que le wrapper {"machines": {}} évite ce piège."""
    client = MagicMock()
    with patch("moveset_optimizer.get_cached", return_value={"machines": {}}):
        result = _move_machines(client, 1)
    assert result == {}
    client.get.assert_not_called()


def test_machine_item_name_cache_hit_skips_http_call():
    """Couvre la branche cache-hit de _machine_item_name (ligne 90) — les tests
    is_hm/method_label ci-dessus ne patchent que le cache-miss."""
    from moveset_optimizer import _machine_item_name

    client = MagicMock()
    with patch("moveset_optimizer.get_cached", return_value={"item": "tm24"}):
        result = _machine_item_name(client, "https://x/machine/1/")

    assert result == "tm24"
    client.get.assert_not_called()


def test_method_label_level_up_is_none():
    assert method_label(MagicMock(), _move(1, method="level-up"), VG) is None


def test_method_label_egg_and_tutor():
    assert method_label(MagicMock(), _move(1, method="egg"), VG) == "Œuf"
    assert method_label(MagicMock(), _move(1, method="tutor"), VG) == "Tuteur"


def test_method_label_machine_resolves_ct_or_cs():
    client = MagicMock()
    client.get.side_effect = [
        _http_resp(
            200,
            {
                "machines": [
                    {
                        "machine": {"url": "https://x/machine/1/"},
                        "version_group": {"name": VG},
                    }
                ]
            },
        ),
        _http_resp(200, {"item": {"name": "tm24"}}),
    ]
    with (
        patch("moveset_optimizer.get_cached", return_value=None),
        patch("moveset_optimizer.set_cache"),
    ):
        assert method_label(client, _move(1, method="machine"), VG) == "CT24"


# ── Dépendances (Dévorêve/Cauchemar) ────────────────────────────────────────


def test_has_enabler_true_when_movepool_contains_matching_ailment():
    movepool = [_move(1, ailment="sleep"), _move(2, ailment=None)]
    assert _has_enabler(movepool, "sleep") is True


def test_has_enabler_false_when_no_match():
    movepool = [_move(1, ailment=None), _move(2, ailment="poison")]
    assert _has_enabler(movepool, "sleep") is False


# ── recommend_moveset (bout en bout) ────────────────────────────────────────


def test_recommend_moveset_filters_out_other_versions():
    pokemon = MagicMock(attack=50, sp_attack=135, generation=1)
    movepool = [
        _move(1, damage_class="special", power=100, version_group="red-blue"),
        _move(2, damage_class="special", power=90, version_group=VG),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    assert [m["id"] for m in result] == [2]


def test_recommend_moveset_attacker_excludes_status_and_off_class():
    """Alakazam (spécial dominant) : attaques physiques et de statut exclues."""
    pokemon = MagicMock(attack=50, sp_attack=135, generation=1)
    movepool = [
        _move(1, damage_class="physical", power=100),
        _move(2, damage_class="special", power=90),
        _move(3, damage_class="special", power=80),
        _move(4, damage_class="special", power=70),
        _move(5, damage_class="status", power=None, pp=20),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    assert len(result) == 3  # seulement 3 attaques spéciales disponibles
    assert all(m["damage_class"] == "special" for m in result)


def test_recommend_moveset_support_prioritizes_status_by_pp():
    pokemon = MagicMock(attack=10, sp_attack=75, generation=1)
    movepool = [
        _move(1, damage_class="status", power=None, pp=10),
        _move(2, damage_class="status", power=None, pp=20),
        _move(3, damage_class="special", power=90),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "support", VG, False, False, MagicMock()
        )

    assert [m["id"] for m in result] == [2, 1, 3]


def test_recommend_moveset_versatility_mixes_damage_and_status():
    pokemon = MagicMock(attack=50, sp_attack=50, generation=1)
    movepool = [
        _move(1, damage_class="special", power=100),
        _move(2, damage_class="status", power=None, pp=20),
        _move(3, damage_class="physical", power=90),
        _move(4, damage_class="status", power=None, pp=10),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "versatility", VG, False, False, MagicMock()
        )

    classes = [m["damage_class"] for m in result]
    assert classes.count("status") == 2
    assert len(result) - classes.count("status") == 2


def test_recommend_moveset_deduplicates_before_scoring():
    pokemon = MagicMock(attack=100, sp_attack=50, generation=1)
    movepool = [_move(1, damage_class="physical", power=90)] * 3
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    assert len(result) == 1


def test_recommend_moveset_exclude_hm_removes_hm_moves():
    pokemon = MagicMock(attack=50, sp_attack=135, generation=1)
    movepool = [
        _move(1, damage_class="special", power=100, method="machine"),
        _move(2, damage_class="special", power=90, method="machine"),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with (
        patch("moveset_optimizer._load_type_chart", return_value={}),
        patch("moveset_optimizer.is_hm", side_effect=lambda c, mid, vg: mid == 1),
    ):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, True, False, MagicMock()
        )

    assert [m["id"] for m in result] == [2]


def test_recommend_moveset_sets_method_label_on_selected_moves():
    pokemon = MagicMock(attack=100, sp_attack=50, generation=1)
    movepool = [_move(1, damage_class="physical", power=90, method="egg")]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    assert result[0]["method_label"] == "Œuf"


def test_recommend_moveset_exclude_tm_removes_tm_moves():
    """Symétrique de exclude_hm : retire les CT (is_hm=False), garde les CS."""
    pokemon = MagicMock(attack=50, sp_attack=135, generation=1)
    movepool = [
        _move(1, damage_class="special", power=100, method="machine"),
        _move(2, damage_class="special", power=90, method="machine"),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with (
        patch("moveset_optimizer._load_type_chart", return_value={}),
        patch("moveset_optimizer.is_hm", side_effect=lambda c, mid, vg: mid == 1),
    ):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, True, MagicMock()
        )

    assert [m["id"] for m in result] == [1]  # move 1 est CS (is_hm True) → conservé


def test_recommend_moveset_excludes_dependent_move_without_enabler():
    """Dévorêve (id 138) sans aucune attaque infligeant le sommeil disponible
    → exclue des candidats — c'est le cas Alakazam Gen 2 qui a motivé ce test."""
    pokemon = MagicMock(attack=50, sp_attack=135, generation=2)
    movepool = [
        _move(138, damage_class="special", power=100, ailment=None),
        _move(2, damage_class="special", power=90, ailment=None),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    assert 138 not in [m["id"] for m in result]


def test_recommend_moveset_keeps_dependent_move_with_enabler():
    """Même Dévorêve, mais Hypnose (ailment=sleep) est disponible → conservée,
    et la justification mentionne la dépendance."""
    pokemon = MagicMock(attack=50, sp_attack=135, generation=2)
    movepool = [
        _move(138, damage_class="special", power=100, ailment=None),
        _move(95, damage_class="status", power=None, ailment="sleep"),
    ]
    db = _make_db([MagicMock(id=1, name="normal")])

    with patch("moveset_optimizer._load_type_chart", return_value={}):
        result = recommend_moveset(
            db, pokemon, movepool, "attacker", VG, False, False, MagicMock()
        )

    dream_eater = next(m for m in result if m["id"] == 138)
    assert "endormie" in dream_eater["reason"]
