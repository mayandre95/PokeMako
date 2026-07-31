from typing import Annotated

import pandas as pd
from cache.redis import get_cached, set_cache
from database import get_db
from fastapi import APIRouter, Depends, Request
from limiter import limiter
from models import Pokemon, PokemonScore, PokemonType, Type
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter(prefix="/analytics", tags=["Analytics"])
RATE_LIMIT = "30/minute"
TTL = 60 * 60 * 24  # 24h


@router.get("/types")
@limiter.limit(RATE_LIMIT)
def get_type_distribution(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Nombre de Pokémon par type, trié du plus au moins représenté."""
    cache_key = "analytics:types"
    if cached := get_cached(cache_key):
        return cached

    rows = (
        db.query(Type.name, func.count(PokemonType.pokemon_id).label("count"))
        .join(PokemonType, Type.id == PokemonType.type_id)
        .group_by(Type.name)
        .order_by(func.count(PokemonType.pokemon_id).desc())
        .all()
    )
    result = [{"type": r.name, "count": r.count} for r in rows]
    set_cache(cache_key, result, ttl=TTL)
    return result


@router.get("/generations")
@limiter.limit(RATE_LIMIT)
def get_generation_stats(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Stats moyennes (hp, attack, …) par génération via pandas."""
    cache_key = "analytics:generations"
    if cached := get_cached(cache_key):
        return cached

    pokemons = db.query(Pokemon).all()

    rows = [
        {
            "generation": p.generation,
            "hp": p.hp,
            "attack": p.attack,
            "defense": p.defense,
            "sp_attack": p.sp_attack,
            "sp_defense": p.sp_defense,
            "speed": p.speed,
        }
        for p in pokemons
        if p.generation is not None
    ]
    if not rows:
        return []

    df = pd.DataFrame(rows)
    stats = (
        df.groupby("generation")[
            ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
        ]
        .mean()
        .round(1)
        .reset_index()
    )
    result = stats.to_dict(orient="records")
    set_cache(cache_key, result, ttl=TTL)
    return result


@router.get("/scatter")
@limiter.limit(RATE_LIMIT)
def get_scatter_data(request: Request, db: Annotated[Session, Depends(get_db)]):
    """Un point par Pokémon : nom, speed, power_score, type primaire (pour colorer)."""
    cache_key = "analytics:scatter"
    if cached := get_cached(cache_key):
        return cached

    rows = (
        db.query(Pokemon, PokemonScore, Type.name.label("primary_type"))
        .join(PokemonScore, Pokemon.id == PokemonScore.pokemon_id)
        .outerjoin(
            PokemonType,
            (Pokemon.id == PokemonType.pokemon_id) & (PokemonType.slot == 1),
        )
        .outerjoin(Type, PokemonType.type_id == Type.id)
        .filter(Pokemon.speed.isnot(None))
        .all()
    )
    result = [
        {
            "name": r.Pokemon.name_fr or r.Pokemon.name_en,
            "speed": r.Pokemon.speed,
            "power_score": r.PokemonScore.power_score,
            "primary_type": r.primary_type,
        }
        for r in rows
    ]
    set_cache(cache_key, result, ttl=TTL)
    return result
