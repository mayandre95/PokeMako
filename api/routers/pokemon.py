from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from cache.redis import get_cached, set_cache
from database import get_db
from models import Pokemon
from schemas.pokemon import PokemonResponse

router = APIRouter(prefix="/pokemon", tags=["pokemon"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get(
    "/{pokemon_id}",
    response_model=PokemonResponse,
    responses={404: {"description": "Pokémon introuvable"}},
)
def get_pokemon(pokemon_id: int, db: DbSession):
    cache_key = f"pokemon:{pokemon_id}"

    if cached := get_cached(cache_key):
        return cached

    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon introuvable")

    response = PokemonResponse.model_validate(pokemon).model_dump()
    set_cache(cache_key, response)
    return response
