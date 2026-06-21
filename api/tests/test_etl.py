import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "etl"))

import fetch_pokemon

POKEMON_FIXTURE = {
    "id": 1,
    "name": "bulbasaur",
    "base_experience": 64,
    "height": 7,
    "weight": 69,
    "sprites": {
        "front_default": "https://example.com/1.png",
        "other": {
            "official-artwork": {"front_default": "https://example.com/artwork/1.png"}
        },
    },
    "species": {"url": "https://pokeapi.co/api/v2/pokemon-species/1/"},
    "stats": [
        {"stat": {"name": "hp"}, "base_stat": 45},
        {"stat": {"name": "attack"}, "base_stat": 49},
        {"stat": {"name": "defense"}, "base_stat": 49},
        {"stat": {"name": "special-attack"}, "base_stat": 65},
        {"stat": {"name": "special-defense"}, "base_stat": 65},
        {"stat": {"name": "speed"}, "base_stat": 45},
    ],
    "types": [
        {"slot": 1, "type": {"name": "grass", "url": ".../12/"}},
        {"slot": 2, "type": {"name": "poison", "url": ".../4/"}},
    ],
    "abilities": [
        {"ability": {"name": "overgrow", "url": ".../1/"}, "is_hidden": False},
    ],
    "moves": [
        {
            "move": {"name": "tackle", "url": ".../33/"},
            "version_group_details": [
                {"move_learn_method": {"name": "level-up"}, "level_learned_at": 1}
            ],
        }
    ],
}

SPECIES_FIXTURE = {
    "generation": {"url": "https://pokeapi.co/api/v2/generation/1/"},
    "is_legendary": False,
    "is_mythical": False,
    "names": [
        {"language": {"name": "en"}, "name": "Bulbasaur"},
        {"language": {"name": "fr"}, "name": "Bulbizarre"},
    ],
}


# --- Tests unitaires (sans base de données) ---


def test_fetch_json_success():
    client = MagicMock(spec=httpx.Client)
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ok": True}
    mock_resp.raise_for_status.return_value = None
    client.get.return_value = mock_resp

    result = fetch_pokemon.fetch_json(client, "http://example.com")
    assert result == {"ok": True}


def test_fetch_json_retries_on_network_error():
    """fetch_json doit retenter après une erreur réseau passagère."""
    client = MagicMock(spec=httpx.Client)
    mock_ok = MagicMock()
    mock_ok.json.return_value = {"retry": True}
    mock_ok.raise_for_status.return_value = None
    client.get.side_effect = [httpx.RequestError("timeout"), mock_ok]

    with patch("fetch_pokemon.time.sleep"):
        result = fetch_pokemon.fetch_json(client, "http://example.com")

    assert result == {"retry": True}
    assert client.get.call_count == 2


def test_pokemon_name_property_prefers_french():
    from models import Pokemon

    p = Pokemon(name_en="Bulbasaur", name_fr="Bulbizarre")
    assert p.name == "Bulbizarre"


def test_pokemon_name_property_falls_back_to_english():
    from models import Pokemon

    p = Pokemon(name_en="Bulbasaur", name_fr=None)
    assert p.name == "Bulbasaur"


def test_process_pokemon_commits_once():
    """process_pokemon doit commiter exactement une fois par Pokémon."""
    client = MagicMock(spec=httpx.Client)
    db = MagicMock()

    with (
        patch(
            "fetch_pokemon.fetch_json", side_effect=[POKEMON_FIXTURE, SPECIES_FIXTURE]
        ),
        patch("fetch_pokemon.time.sleep"),
        patch("fetch_pokemon._upsert_type", return_value=1),
        patch("fetch_pokemon._upsert_ability"),
        patch("fetch_pokemon._upsert_move"),
    ):
        fetch_pokemon.process_pokemon(client, db, 1)

    db.commit.assert_called_once()


def test_fetch_json_raises_after_max_retries():
    """fetch_json doit propager l'exception après MAX_RETRIES échecs."""
    client = MagicMock(spec=httpx.Client)
    client.get.side_effect = httpx.RequestError("timeout")

    with patch("fetch_pokemon.time.sleep"):
        try:
            fetch_pokemon.fetch_json(client, "http://example.com")
            assert False, "Aurait dû lever une exception"
        except httpx.RequestError:
            pass

    assert client.get.call_count == fetch_pokemon.MAX_RETRIES


def test_process_pokemon_skips_duplicate_move():
    """process_pokemon doit ignorer un move_id déjà traité (seen_moves)."""
    client = MagicMock(spec=httpx.Client)
    db = MagicMock()

    fixture_with_duplicate_move = {
        **POKEMON_FIXTURE,
        "moves": [
            {
                "move": {"name": "tackle", "url": ".../33/"},
                "version_group_details": [
                    {"move_learn_method": {"name": "level-up"}, "level_learned_at": 1}
                ],
            },
            {
                "move": {"name": "tackle", "url": ".../33/"},  # doublon
                "version_group_details": [
                    {"move_learn_method": {"name": "level-up"}, "level_learned_at": 1}
                ],
            },
        ],
    }

    with (
        patch(
            "fetch_pokemon.fetch_json",
            side_effect=[fixture_with_duplicate_move, SPECIES_FIXTURE],
        ),
        patch("fetch_pokemon.time.sleep"),
        patch("fetch_pokemon._upsert_type", return_value=1),
        patch("fetch_pokemon._upsert_ability"),
        patch("fetch_pokemon._upsert_move") as mock_upsert_move,
    ):
        fetch_pokemon.process_pokemon(client, db, 1)

    mock_upsert_move.assert_called_once()


def test_main_skips_when_db_full():
    """main() ne lance pas l'ETL si la base contient déjà 1025 Pokémon."""
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 1025
    mock_db.__enter__ = lambda s: mock_db
    mock_db.__exit__ = MagicMock(return_value=False)

    with (
        patch("fetch_pokemon.SessionLocal", return_value=mock_db),
        patch("fetch_pokemon.run") as mock_run,
    ):
        fetch_pokemon.main()

    mock_run.assert_not_called()


def test_main_runs_etl_when_db_empty():
    """main() lance l'ETL si la base est vide."""
    mock_db = MagicMock()
    mock_db.query.return_value.count.return_value = 0
    mock_db.__enter__ = lambda s: mock_db
    mock_db.__exit__ = MagicMock(return_value=False)

    with (
        patch("fetch_pokemon.SessionLocal", return_value=mock_db),
        patch("fetch_pokemon.run") as mock_run,
    ):
        fetch_pokemon.main(start=1, end=10)

    mock_run.assert_called_once_with(1, 10)


def test_run_continues_after_pokemon_error():
    """run() doit continuer sur les Pokémon suivants si l'un échoue."""
    mock_db = MagicMock()
    mock_db.__enter__ = lambda s: mock_db
    mock_db.__exit__ = MagicMock(return_value=False)

    call_count = 0

    def process_side_effect(client, db, pid):
        nonlocal call_count
        call_count += 1
        if pid == 1:
            raise ValueError("Erreur simulée")

    with (
        patch("fetch_pokemon.SessionLocal", return_value=mock_db),
        patch("fetch_pokemon.httpx.Client") as mock_client_cls,
        patch("fetch_pokemon.process_pokemon", side_effect=process_side_effect),
    ):
        mock_client_cls.return_value.__enter__ = lambda s: MagicMock()
        mock_client_cls.return_value.__exit__ = MagicMock(return_value=False)
        fetch_pokemon.run(1, 3)

    assert call_count == 3
    mock_db.rollback.assert_called_once()


# --- Test d'intégration (base de données réelle) ---


def test_process_pokemon_inserts_bilingual_names():
    """Intégration : vérifie l'insertion réelle en base avec noms bilingues."""
    from database import SessionLocal
    from models import Pokemon

    client_mock = MagicMock(spec=httpx.Client)

    with SessionLocal() as db:
        with (
            patch(
                "fetch_pokemon.fetch_json",
                side_effect=[POKEMON_FIXTURE, SPECIES_FIXTURE],
            ),
            patch("fetch_pokemon.time.sleep"),
        ):
            fetch_pokemon.process_pokemon(client_mock, db, 1)

        pokemon = db.query(Pokemon).filter_by(id=1).first()
        assert pokemon is not None
        assert pokemon.name_en == "Bulbasaur"
        assert pokemon.name_fr == "Bulbizarre"
        assert pokemon.name == "Bulbizarre"
        assert pokemon.hp == 45
