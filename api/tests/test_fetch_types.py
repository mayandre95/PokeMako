import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "etl"))

import fetch_types

_TYPE_LIST = {
    "results": [
        {"name": "fire", "url": "https://pokeapi.co/api/v2/type/10/"},
        {"name": "unknown"},
        {"name": "shadow"},
    ]
}

_TYPE_DETAIL_NO_PAST = {
    "name": "fire",
    "damage_relations": {
        "double_damage_to": [{"name": "grass"}],
        "half_damage_to": [{"name": "fire"}],
        "no_damage_to": [{"name": "water"}],
    },
    "past_damage_relations": [],
}

_TYPE_DETAIL_WITH_PAST = {
    "name": "fire",
    "damage_relations": {
        "double_damage_to": [{"name": "grass"}],
        "half_damage_to": [],
        "no_damage_to": [],
    },
    "past_damage_relations": [
        {
            "generation": {"name": "generation-v"},
            "damage_relations": {
                "double_damage_to": [],
                "half_damage_to": [{"name": "fire"}],
                "no_damage_to": [],
            },
        }
    ],
}


def _make_type(name, type_id):
    t = MagicMock()
    t.name = name
    t.id = type_id
    return t


def _make_db(type_objs):
    db = MagicMock()
    db.query.return_value.all.return_value = type_objs
    db.__enter__ = lambda s: db
    db.__exit__ = MagicMock(return_value=False)
    return db


def _make_client(type_list_resp, type_detail_resp):
    c = MagicMock()

    def _get(url, **kw):
        r = MagicMock()
        r.json.return_value = (
            type_list_resp if "type?limit" in url else type_detail_resp
        )
        return r

    c.get.side_effect = _get
    c.__enter__ = lambda s: c
    c.__exit__ = MagicMock(return_value=False)
    return c


# ── _parse_relations ──────────────────────────────────────────────────────────


def test_parse_relations_all_categories():
    type_map = {"grass": 1, "fire": 10, "water": 11}
    rels = {
        "double_damage_to": [{"name": "grass"}],
        "half_damage_to": [{"name": "fire"}],
        "no_damage_to": [{"name": "water"}],
    }
    result = fetch_types._parse_relations(rels, type_map)
    assert result == {"grass": 2.0, "fire": 0.5, "water": 0.0}


def test_parse_relations_ignores_unknown_types():
    """Types absents de la DB (ex. stellar) → ignores."""
    type_map = {"grass": 1}
    rels = {
        "double_damage_to": [{"name": "grass"}, {"name": "stellar"}],
        "half_damage_to": [],
        "no_damage_to": [],
    }
    result = fetch_types._parse_relations(rels, type_map)
    assert result == {"grass": 2.0}
    assert "stellar" not in result


# ── run() ─────────────────────────────────────────────────────────────────────


def test_run_inserts_effectiveness_and_commits():
    """run() insere les effets de type en DB et commite."""
    type_objs = [
        _make_type("fire", 10),
        _make_type("grass", 1),
        _make_type("water", 11),
    ]
    db = _make_db(type_objs)
    c = _make_client(_TYPE_LIST, _TYPE_DETAIL_NO_PAST)

    with (
        patch("fetch_types.SessionLocal", return_value=db),
        patch("fetch_types.httpx.Client", return_value=c),
        patch("fetch_types.time.sleep"),
    ):
        fetch_types.run()

    db.commit.assert_called_once()
    db.execute.assert_called()


def test_run_skips_type_absent_from_db():
    """Type retourne par PokéAPI mais absent de la DB → pas d'insertion."""
    type_objs = [_make_type("grass", 1)]  # fire absent
    db = _make_db(type_objs)
    c = _make_client(
        {"results": [{"name": "fire", "url": "https://pokeapi.co/api/v2/type/10/"}]},
        _TYPE_DETAIL_NO_PAST,
    )

    with (
        patch("fetch_types.SessionLocal", return_value=db),
        patch("fetch_types.httpx.Client", return_value=c),
        patch("fetch_types.time.sleep"),
    ):
        fetch_types.run()

    db.commit.assert_called_once()
    db.execute.assert_not_called()


def test_run_skips_unknown_defender_type():
    """Line 83: if not defender_id → skip quand le type defenseur est absent de la DB."""
    type_objs = [_make_type("fire", 10)]  # grass absent de la DB
    db = _make_db(type_objs)
    c = _make_client(
        {"results": [{"name": "fire", "url": "https://pokeapi.co/api/v2/type/10/"}]},
        {
            "name": "fire",
            "damage_relations": {
                "double_damage_to": [{"name": "grass"}],  # grass absent → skip
                "half_damage_to": [],
                "no_damage_to": [],
            },
            "past_damage_relations": [],
        },
    )

    with (
        patch("fetch_types.SessionLocal", return_value=db),
        patch("fetch_types.httpx.Client", return_value=c),
        patch("fetch_types.time.sleep"),
    ):
        fetch_types.run()

    db.commit.assert_called_once()
    db.execute.assert_not_called()


def test_run_handles_past_damage_relations():
    """past_damage_relations → deux entrees timeline pour la meme paire de types."""
    type_objs = [_make_type("fire", 10), _make_type("grass", 1)]
    db = _make_db(type_objs)
    c = _make_client(_TYPE_LIST, _TYPE_DETAIL_WITH_PAST)

    with (
        patch("fetch_types.SessionLocal", return_value=db),
        patch("fetch_types.httpx.Client", return_value=c),
        patch("fetch_types.time.sleep"),
    ):
        fetch_types.run()

    db.commit.assert_called_once()
    # Past (fire→fire ×0.5 depuis gen 1) + current (fire→grass ×2.0 depuis gen 6)
    assert db.execute.call_count == 2
