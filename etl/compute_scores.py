import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "api"))

from database import SessionLocal
from models import Pokemon, PokemonScore, Type
from scoring import (
    _load_type_chart,
    compute_offensive_score,
    compute_power_score,
    compute_role_scores,
    compute_tank_score,
)
from sqlalchemy.dialects.postgresql import insert as pg_insert

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def run():
    with SessionLocal() as db:
        pokemons = db.query(Pokemon).all()

        generations = {p.generation or 1 for p in pokemons}
        charts = {gen: _load_type_chart(db, gen) for gen in generations}
        all_type_ids_list = [t.id for t in db.query(Type).all()]

        for pokemon in pokemons:
            gen = pokemon.generation or 1
            chart = charts[gen]
            type_ids = [pt.type_id for pt in pokemon.types]
            power = compute_power_score(pokemon)

            immunities = resistances = weaknesses = 0
            for attacker_id in all_type_ids_list:
                mult = 1.0
                for defender_id in type_ids:
                    mult *= chart.get((attacker_id, defender_id), 1.0)
                if not mult:
                    immunities += 1
                elif mult < 1.0:
                    resistances += 1
                elif mult > 1.0:
                    weaknesses += 1
            meta = float(power + immunities * 10 + resistances * 5 - weaknesses * 10)

            values = {
                "pokemon_id": pokemon.id,
                "power_score": power,
                "offensive_score": compute_offensive_score(pokemon),
                "tank_score": compute_tank_score(pokemon),
                "meta_score": meta,
                **compute_role_scores(pokemon),
            }
            db.execute(
                pg_insert(PokemonScore)
                .values(**values)
                .on_conflict_do_update(index_elements=["pokemon_id"], set_=values)
            )

        db.commit()
        log.info("Scores calculés pour %d Pokémon.", len(pokemons))


if __name__ == "__main__":
    run()
