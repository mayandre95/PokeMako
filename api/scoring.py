from sqlalchemy import func
from sqlalchemy.orm import Session

from models import Type, TypeEffectiveness


def _load_type_chart(db: Session, generation: int) -> dict[tuple[int, int], float]:
    subq = (
        db.query(
            TypeEffectiveness.attacker_type_id,
            TypeEffectiveness.defender_type_id,
            func.max(TypeEffectiveness.from_generation).label("max_gen"),
        )
        .filter(TypeEffectiveness.from_generation <= generation)
        .group_by(
            TypeEffectiveness.attacker_type_id, TypeEffectiveness.defender_type_id
        )
        .subquery()
    )
    rows = (
        db.query(TypeEffectiveness)
        .join(
            subq,
            (TypeEffectiveness.attacker_type_id == subq.c.attacker_type_id)
            & (TypeEffectiveness.defender_type_id == subq.c.defender_type_id)
            & (TypeEffectiveness.from_generation == subq.c.max_gen),
        )
        .all()
    )
    return {(r.attacker_type_id, r.defender_type_id): r.multiplier for r in rows}


def compute_power_score(pokemon) -> int:
    stats = [
        pokemon.hp,
        pokemon.attack,
        pokemon.defense,
        pokemon.sp_attack,
        pokemon.sp_defense,
        pokemon.speed,
    ]
    return sum(s for s in stats if s is not None)


def compute_offensive_score(pokemon) -> int:
    return (pokemon.attack or 0) + (pokemon.sp_attack or 0) + (pokemon.speed or 0)


def compute_tank_score(pokemon) -> int:
    return (pokemon.hp or 0) + (pokemon.defense or 0) + (pokemon.sp_defense or 0)


def compute_meta_score(
    db: Session,
    power: int,
    pokemon_type_ids: list[int],
    generation: int,
) -> float:
    # Utiliser _load_type_chart() en dehors de la boucle lorsque plusieurs Pokémon
    # d'une même génération sont traités en lot (ETL) — évite N requêtes DB.
    chart = _load_type_chart(db, generation)
    all_type_ids = [t.id for t in db.query(Type).all()]

    immunities = resistances = weaknesses = 0
    for attacker_id in all_type_ids:
        mult = 1.0
        for defender_id in pokemon_type_ids:
            mult *= chart.get((attacker_id, defender_id), 1.0)
        if mult == 0.0:
            immunities += 1
        elif mult < 1.0:
            resistances += 1
        elif mult > 1.0:
            weaknesses += 1

    bonus = immunities * 10 + resistances * 5 - weaknesses * 10
    return float(power + bonus)
