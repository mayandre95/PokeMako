from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from main import app
from routers.moves import _move_detail

client = TestClient(app)

_SAMPLE_POKEMON = {
    "moves": [
        {
            "move": {"name": "tackle", "url": "https://pokeapi.co/api/v2/move/33/"},
            "version_group_details": [
                {
                    "level_learned_at": 1,
                    "move_learn_method": {"name": "level-up"},
                    "version_group": {"name": "red-blue"},
                }
            ],
        }
    ]
}

_SAMPLE_MOVE = {
    "id": 33,
    "name": "tackle",
    "type": {"name": "normal"},
    "damage_class": {"name": "physical"},
    "power": 40,
    "accuracy": 100,
    "pp": 35,
    "effect_chance": None,
    "names": [
        {"language": {"name": "en"}, "name": "Tackle"},
        {"language": {"name": "fr"}, "name": "Charge"},
    ],
    "effect_entries": [
        {
            "language": {"name": "fr"},
            "short_effect": "Inflige des dégâts normaux.",
        },
        {
            "language": {"name": "en"},
            "short_effect": "Inflicts regular damage.",
        },
    ],
}


def _http_resp(status=200, data=None):
    r = MagicMock()
    r.status_code = status
    r.json.return_value = data if data is not None else {}
    r.raise_for_status = MagicMock()
    return r


def _mock_httpx(pokemon_resp, move_resp=None):
    mock_instance = MagicMock()

    def _get(url, **kw):
        if "/move/" in url:
            return move_resp or _http_resp(200, _SAMPLE_MOVE)
        return pokemon_resp

    mock_instance.get.side_effect = _get
    mock_instance.__enter__ = lambda s: mock_instance
    mock_instance.__exit__ = MagicMock(return_value=False)
    return MagicMock(return_value=mock_instance)


# ── _move_detail ────────────────────────────────────────────────────────────


def test_move_detail_cache_hit():
    cached = {
        "name_fr": "Charge",
        "name_en": "Tackle",
        "type": "normal",
        "damage_class": "physical",
        "power": 40,
        "accuracy": 100,
        "pp": 35,
        "effect_fr": None,
        "effect_en": None,
        "id": 33,
    }
    with patch("routers.moves.get_cached", return_value=cached):
        result = _move_detail(MagicMock(), 33)
    assert result["name_fr"] == "Charge"


def test_move_detail_found():
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, _SAMPLE_MOVE)
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache") as mock_set,
    ):
        result = _move_detail(mock_client, 33)
    assert result["name_fr"] == "Charge"
    assert result["power"] == 40
    assert result["ailment"] is None  # pas de clé "meta" du tout dans le fixture
    mock_set.assert_called_once()


def test_move_detail_extracts_ailment_from_meta():
    move_with_meta = {**_SAMPLE_MOVE, "meta": {"ailment": {"name": "sleep"}}}
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, move_with_meta)
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache"),
    ):
        result = _move_detail(mock_client, 33)
    assert result["ailment"] == "sleep"


def test_move_detail_handles_null_meta():
    """PokéAPI renvoie parfois "meta": null explicitement (pas juste absent)
    — .get("meta", {}) ne rattraperait pas ce cas, seul `or {}` le fait."""
    move_with_null_meta = {**_SAMPLE_MOVE, "meta": None}
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, move_with_null_meta)
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache"),
    ):
        result = _move_detail(mock_client, 33)
    assert result["ailment"] is None


def test_move_detail_api_error():
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(404)
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache") as mock_set,
    ):
        result = _move_detail(mock_client, 9999)
    assert result is None
    mock_set.assert_not_called()


# ── GET /pokemon/{id}/moves ─────────────────────────────────────────────────


def test_get_moves_from_cache():
    cached = {"moves": []}
    with patch("routers.pokemon.get_cached", return_value=cached):
        resp = client.get("/pokemon/25/moves")
    assert resp.status_code == 200
    assert resp.json()["moves"] == []


def test_get_moves_from_api():
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch("routers.moves.set_cache"),
        patch(
            "routers.pokemon.httpx.Client",
            _mock_httpx(
                _http_resp(200, _SAMPLE_POKEMON), _http_resp(200, _SAMPLE_MOVE)
            ),
        ),
    ):
        resp = client.get("/pokemon/25/moves")

    assert resp.status_code == 200
    data = resp.json()
    assert data["moves"][0]["name_fr"] == "Charge"
    assert data["moves"][0]["version_group"] == "red-blue"
    assert data["moves"][0]["level_learned"] == 1


def test_get_moves_not_found():
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.pokemon.httpx.Client", _mock_httpx(_http_resp(404))),
    ):
        resp = client.get("/pokemon/99999/moves")
    assert resp.status_code == 404


# ── GET /move/{id} ──────────────────────────────────────────────────────────


def test_get_move_detail():
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache"),
        patch(
            "routers.moves.httpx.Client",
            _mock_httpx(MagicMock(), _http_resp(200, _SAMPLE_MOVE)),
        ),
    ):
        resp = client.get("/move/33")

    assert resp.status_code == 200
    data = resp.json()
    assert data["name_fr"] == "Charge"
    assert data["effect_fr"] == "Inflige des dégâts normaux."


def test_get_move_not_found():
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch(
            "routers.moves.httpx.Client",
            _mock_httpx(MagicMock(), _http_resp(404)),
        ),
    ):
        resp = client.get("/move/99999")
    assert resp.status_code == 404


def test_move_detail_effect_chance_substitution():
    """Non-null effect_chance → $effect_chance$ replaced in FR and EN effect texts."""
    move_with_chance = {
        **_SAMPLE_MOVE,
        "effect_chance": 30,
        "effect_entries": [
            {
                "language": {"name": "fr"},
                "short_effect": "A $effect_chance$% de chances.",
            },
            {
                "language": {"name": "en"},
                "short_effect": "Has a $effect_chance$% chance.",
            },
        ],
    }
    mock_client = MagicMock()
    mock_client.get.return_value = _http_resp(200, move_with_chance)
    with (
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.moves.set_cache"),
    ):
        result = _move_detail(mock_client, 33)
    assert result["effect_fr"] == "A 30% de chances."
    assert result["effect_en"] == "Has a 30% chance."


def test_get_moves_min_level_dedup():
    """Same move + version_group listed twice as level-up → minimum level is kept."""
    pokemon_with_dup = {
        "moves": [
            {
                "move": {"name": "tackle", "url": "https://pokeapi.co/api/v2/move/33/"},
                "version_group_details": [
                    {
                        "level_learned_at": 5,
                        "move_learn_method": {"name": "level-up"},
                        "version_group": {"name": "red-blue"},
                    },
                    {
                        "level_learned_at": 1,
                        "move_learn_method": {"name": "level-up"},
                        "version_group": {"name": "red-blue"},
                    },
                ],
            }
        ]
    }
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch("routers.moves.set_cache"),
        patch(
            "routers.pokemon.httpx.Client",
            _mock_httpx(
                _http_resp(200, pokemon_with_dup), _http_resp(200, _SAMPLE_MOVE)
            ),
        ),
    ):
        resp = client.get("/pokemon/25/moves")
    assert resp.status_code == 200
    moves = resp.json()["moves"]
    assert len(moves) == 1
    assert moves[0]["level_learned"] == 1


def test_get_moves_skips_missing_detail():
    """_move_detail returns None (API 404) → move is skipped via continue."""
    with (
        patch("routers.pokemon.get_cached", return_value=None),
        patch("routers.moves.get_cached", return_value=None),
        patch("routers.pokemon.set_cache"),
        patch("routers.moves.set_cache"),
        patch(
            "routers.pokemon.httpx.Client",
            _mock_httpx(_http_resp(200, _SAMPLE_POKEMON), _http_resp(404)),
        ),
    ):
        resp = client.get("/pokemon/25/moves")
    assert resp.status_code == 200
    assert resp.json()["moves"] == []
