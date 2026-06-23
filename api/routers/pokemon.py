from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from limiter import limiter
from models import Pokemon
from schemas.pokemon import PokemonResponse
from sqlalchemy.orm import Session

router = APIRouter(prefix="/pokemon", tags=["Pokémon"])

RATE_LIMIT = "30/minute"


@router.get(
    "/{pokemon_id}",
    response_model=PokemonResponse,
    responses={429: {"description": "Trop de requêtes — réessayez dans 60s"}},
)
@limiter.limit(RATE_LIMIT)
def get_pokemon(
    request: Request, pokemon_id: int, db: Annotated[Session, Depends(get_db)]
):
    cache_key = f"pokemon:{pokemon_id}"

    if cached := get_cached(cache_key):
        return cached

    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon introuvable")

    response = PokemonResponse.model_validate(pokemon).model_dump()
    set_cache(cache_key, response)
    return response
