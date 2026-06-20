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
