import argparse
import logging
import sys
import time
from pathlib import Path

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Rend les modules api/ (database, models) importables depuis etl/
sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from database import SessionLocal
from models import (
    Ability,
    Move,
    Pokemon,
    PokemonAbility,
    PokemonMove,
    PokemonType,
    Type,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE_URL = "https://pokeapi.co/api/v2"
DELAY = 0.3  # secondes entre chaque requête (rate limiting)
MAX_RETRIES = 3


def main(start: int = 1, end: int = 1025) -> None:
    with SessionLocal() as db:
        if db.query(Pokemon).count() >= 1025:
            log.info("Base déjà peuplée — ETL ignoré.")
            return
    run(start, end)


def fetch_json(client: httpx.Client, url: str) -> dict:
    for attempt in range(MAX_RETRIES):
        try:
            r = client.get(url, timeout=30)
            r.raise_for_status()
            return r.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            wait = 2**attempt
            log.warning(
                "Retry %d/%d — %s (attente %ds)", attempt + 1, MAX_RETRIES, exc, wait
            )
            time.sleep(wait)
    return {}


def _upsert_type(db, name: str) -> int:
    db.execute(
        pg_insert(Type)
        .values(name=name)
        .on_conflict_do_nothing(index_elements=["name"])
    )
    db.flush()
    return db.query(Type).filter_by(name=name).one().id


def _upsert_ability(db, ab_id: int, name: str) -> None:
    db.execute(
        pg_insert(Ability)
        .values(id=ab_id, name=name)
        .on_conflict_do_update(index_elements=["id"], set_={"name": name})
    )


def _upsert_move(db, move_id: int, name: str) -> None:
    db.execute(
        pg_insert(Move)
        .values(id=move_id, name=name)
        .on_conflict_do_update(index_elements=["id"], set_={"name": name})
    )


def process_pokemon(client: httpx.Client, db, pokemon_id: int) -> None:
    data = fetch_json(client, f"{BASE_URL}/pokemon/{pokemon_id}")
    time.sleep(DELAY)
    species = fetch_json(client, data["species"]["url"])
    time.sleep(DELAY)

    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    gen = int(species["generation"]["url"].rstrip("/").split("/")[-1])

    names = {n["language"]["name"]: n["name"] for n in species.get("names", [])}
    name_en = names.get("en") or data["name"]
    name_fr = names.get("fr")

    pokemon_values = {
        "id": data["id"],
        "name_en": name_en,
        "name_fr": name_fr,
        "base_experience": data.get("base_experience"),
        "height": data["height"],
        "weight": data["weight"],
        "sprite_url": (data["sprites"] or {}).get("front_default"),
        "artwork_url": (
            (data["sprites"].get("other") or {})
            .get("official-artwork", {})
            .get("front_default")
        ),
        "generation": gen,
        "is_legendary": species["is_legendary"],
        "is_mythical": species["is_mythical"],
        "hp": stats.get("hp"),
        "attack": stats.get("attack"),
        "defense": stats.get("defense"),
        "sp_attack": stats.get("special-attack"),
        "sp_defense": stats.get("special-defense"),
        "speed": stats.get("speed"),
    }
    db.execute(
        pg_insert(Pokemon)
        .values(**pokemon_values)
        .on_conflict_do_update(index_elements=["id"], set_=pokemon_values)
    )

    # Suppression puis réinsertion des relations — plus simple que l'upsert sur tables de jonction
    db.query(PokemonType).filter_by(pokemon_id=data["id"]).delete()
    db.query(PokemonAbility).filter_by(pokemon_id=data["id"]).delete()
    db.query(PokemonMove).filter_by(pokemon_id=data["id"]).delete()

    for slot in data["types"]:
        type_id = _upsert_type(db, slot["type"]["name"])
        db.add(PokemonType(pokemon_id=data["id"], type_id=type_id, slot=slot["slot"]))

    for ab in data["abilities"]:
        ab_id = int(ab["ability"]["url"].rstrip("/").split("/")[-1])
        _upsert_ability(db, ab_id, ab["ability"]["name"])
        db.add(
            PokemonAbility(
                pokemon_id=data["id"],
                ability_id=ab_id,
                is_hidden=ab["is_hidden"],
            )
        )

    seen_moves: set[int] = set()
    for mv in data["moves"]:
        move_id = int(mv["move"]["url"].rstrip("/").split("/")[-1])
        if move_id in seen_moves:
            continue
        for vd in mv["version_group_details"]:
            if vd["move_learn_method"]["name"] == "level-up":
                _upsert_move(db, move_id, mv["move"]["name"])
                db.add(
                    PokemonMove(
                        pokemon_id=data["id"],
                        move_id=move_id,
                        learn_method="level-up",
                        level_learned=vd["level_learned_at"],
                    )
                )
                seen_moves.add(move_id)
                break  # une seule entrée par move (premier groupe de version)

    db.commit()
    log.info("[%4d/1025] %-20s / %-20s gen%d", data["id"], name_fr or "—", name_en, gen)


def run(start: int, end: int) -> None:
    log.info("ETL PokéMako — Pokémon %d → %d", start, end)
    with SessionLocal() as db:
        with httpx.Client() as client:
            for pid in range(start, end + 1):
                try:
                    process_pokemon(client, db, pid)
                except Exception as exc:
                    log.error("Pokémon #%d échoué : %s", pid, exc)
                    db.rollback()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL PokéAPI → PostgreSQL")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1025)
    args = parser.parse_args()
    main(args.start, args.end)
