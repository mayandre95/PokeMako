import logging
import sys
import time
from pathlib import Path

import httpx
from sqlalchemy.dialects.postgresql import insert as pg_insert

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from database import SessionLocal
from models import Type, TypeEffectiveness

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

BASE_URL = "https://pokeapi.co/api/v2"

GENERATION_TO_INT = {
    "generation-i": 1,
    "generation-ii": 2,
    "generation-iii": 3,
    "generation-iv": 4,
    "generation-v": 5,
    "generation-vi": 6,
    "generation-vii": 7,
    "generation-viii": 8,
    "generation-ix": 9,
}

# Génération d'introduction des types absents en Gen 1
TYPE_INTRODUCED_IN = {"dark": 2, "steel": 2, "fairy": 6}


def _parse_relations(damage_relations: dict, type_name_to_id: dict) -> dict[str, float]:
    rules: dict[str, float] = {}
    for t in damage_relations.get("double_damage_to", []):
        if t["name"] in type_name_to_id:
            rules[t["name"]] = 2.0
    for t in damage_relations.get("half_damage_to", []):
        if t["name"] in type_name_to_id:
            rules[t["name"]] = 0.5
    for t in damage_relations.get("no_damage_to", []):
        if t["name"] in type_name_to_id:
            rules[t["name"]] = 0.0
    return rules


def run():
    with SessionLocal() as db:
        with httpx.Client(timeout=15) as client:
            resp = client.get(f"{BASE_URL}/type?limit=30")
            type_entries = [
                t
                for t in resp.json()["results"]
                if t["name"] not in ("unknown", "shadow")
            ]
            type_name_to_id = {t.name: t.id for t in db.query(Type).all()}

            for entry in type_entries:
                resp = client.get(entry["url"])
                data = resp.json()
                attacker_name = data["name"]
                attacker_id = type_name_to_id.get(attacker_name)
                if not attacker_id:
                    log.warning(
                        "Type %s absent de la DB — lancer l'ETL Pokémon d'abord.",
                        attacker_name,
                    )
                    continue

                introduced_gen = TYPE_INTRODUCED_IN.get(attacker_name, 1)

                past_entries = sorted(
                    data.get("past_damage_relations", []),
                    key=lambda x: GENERATION_TO_INT.get(x["generation"]["name"], 0),
                )

                timeline = []
                prev_from_gen = introduced_gen
                for past in past_entries:
                    timeline.append(
                        (
                            prev_from_gen,
                            _parse_relations(past["damage_relations"], type_name_to_id),
                        )
                    )
                    prev_from_gen = GENERATION_TO_INT[past["generation"]["name"]] + 1

                timeline.append(
                    (
                        prev_from_gen,
                        _parse_relations(data["damage_relations"], type_name_to_id),
                    )
                )

                for from_gen, rules in timeline:
                    for defender_name, multiplier in rules.items():
                        defender_id = type_name_to_id[defender_name]
                        db.execute(
                            pg_insert(TypeEffectiveness)
                            .values(
                                attacker_type_id=attacker_id,
                                defender_type_id=defender_id,
                                multiplier=multiplier,
                                from_generation=from_gen,
                            )
                            .on_conflict_do_update(
                                index_elements=[
                                    "attacker_type_id",
                                    "defender_type_id",
                                    "from_generation",
                                ],
                                set_={"multiplier": multiplier},
                            )
                        )

                time.sleep(0.1)
                log.info("Types traités : %s", attacker_name)

        db.commit()
        log.info("type_effectiveness peuplée.")


if __name__ == "__main__":
    run()
