from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from limiter import limiter
from models import Pokemon, PokemonScore, Type
from scoring import _load_type_chart
from sqlalchemy.orm import Session

router = APIRouter(prefix="/pokemon", tags=["Scores"])

RATE_LIMIT = "30/minute"
NOT_FOUND_DETAIL = "Scores introuvables"


@router.get(
    "/{pokemon_id}/scores",
    responses={
        404: {"description": NOT_FOUND_DETAIL},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def get_scores(
    request: Request,
    pokemon_id: int,
    generation: int | None = None,
    db: Annotated[Session, Depends(get_db)] = None,
):
    cache_key = f"scores:{pokemon_id}:{generation or 'default'}"
    if cached := get_cached(cache_key):
        return cached

    score = db.query(PokemonScore).filter_by(pokemon_id=pokemon_id).first()
    if not score:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    pokemon = db.query(Pokemon).filter_by(id=pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    if generation is not None:
        type_ids = [pt.type_id for pt in pokemon.types]
        all_type_ids = [t.id for t in db.query(Type).all()]
        chart = _load_type_chart(db, generation)
        power = score.power_score
        immunities = resistances = weaknesses = 0
        for attacker_id in all_type_ids:
            mult = 1.0
            for defender_id in type_ids:
                mult *= chart.get((attacker_id, defender_id), 1.0)
            if mult == 0.0:
                immunities += 1
            elif mult < 1.0:
                resistances += 1
            elif mult > 1.0:
                weaknesses += 1
        meta = float(power + immunities * 10 + resistances * 5 - weaknesses * 10)
        generation_used = generation
    else:
        meta = score.meta_score
        generation_used = pokemon.generation

    result = {
        "pokemon_id": pokemon_id,
        "power_score": score.power_score,
        "offensive_score": score.offensive_score,
        "tank_score": score.tank_score,
        "meta_score": meta,
        "generation_used": generation_used,
    }
    set_cache(cache_key, result, ttl=60 * 60 * 24)
    return result
