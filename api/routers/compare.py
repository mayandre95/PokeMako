from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from fastapi import APIRouter, Depends, Request
from limiter import limiter
from models import Pokemon, PokemonScore, PokemonType
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

router = APIRouter(tags=["Compare"])
RATE_LIMIT = "30/minute"


@router.get("/search")
@limiter.limit(RATE_LIMIT)
def search_pokemon(
    request: Request,
    q: str,
    limit: int = 10,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Recherche autocomplete par nom FR ou EN."""
    if len(q) < 2:
        return []
    pattern = f"%{q}%"
    # unaccent() des deux côtés : "leviator" doit trouver "Léviator" sans que
    # l'utilisateur ait à taper l'accent (extension Postgres, cf. migration).
    results = (
        db.query(Pokemon)
        .filter(
            or_(
                func.unaccent(Pokemon.name_fr).ilike(func.unaccent(pattern)),
                func.unaccent(Pokemon.name_en).ilike(func.unaccent(pattern)),
            )
        )
        .limit(min(limit, 20))
        .all()
    )
    return [
        {
            "id": p.id,
            "name_fr": p.name_fr,
            "name_en": p.name_en,
            "sprite_url": p.sprite_url,
        }
        for p in results
    ]


@router.get("/compare")
@limiter.limit(RATE_LIMIT)
def compare_pokemon(
    request: Request,
    ids: str,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Stats + scores pour une liste d'IDs (max 3, séparés par virgule)."""
    cache_key = f"compare:{ids}"
    if cached := get_cached(cache_key):
        return cached

    id_list = [int(i) for i in ids.split(",") if i.strip().isdigit()][:3]
    if not id_list:
        return []

    pokemons = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types).joinedload(PokemonType.type))
        .filter(Pokemon.id.in_(id_list))
        .all()
    )
    scores = {
        s.pokemon_id: s
        for s in db.query(PokemonScore)
        .filter(PokemonScore.pokemon_id.in_(id_list))
        .all()
    }

    # Conserver l'ordre demandé dans l'URL
    pokemon_map = {p.id: p for p in pokemons}
    result = []
    for pid in id_list:
        p = pokemon_map.get(pid)
        if not p:
            continue
        s = scores.get(pid)
        result.append(
            {
                "id": p.id,
                "name_fr": p.name_fr,
                "name_en": p.name_en,
                "sprite_url": p.sprite_url,
                "types": [pt.type.name for pt in p.types],
                "hp": p.hp,
                "attack": p.attack,
                "defense": p.defense,
                "sp_attack": p.sp_attack,
                "sp_defense": p.sp_defense,
                "speed": p.speed,
                "power_score": s.power_score if s else None,
                "offensive_score": s.offensive_score if s else None,
                "tank_score": s.tank_score if s else None,
                "meta_score": s.meta_score if s else None,
            }
        )

    set_cache(cache_key, result, ttl=60 * 60)  # TTL 1h (les scores peuvent changer)
    return result
