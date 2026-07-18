from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated

from cache.redis import get_cached, set_cache
from database import get_db
from limiter import limiter
from models import Pokemon
from schemas.pokemon import PokemonResponse
from sqlalchemy.orm import Session, joinedload
import httpx

router = APIRouter(prefix="/pokemon", tags=["Pokémon"])

RATE_LIMIT = "30/minute"
POKEAPI = "https://pokeapi.co/api/v2"


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

    pokemon = (
        db.query(Pokemon)
        .options(joinedload(Pokemon.types))
        .filter(Pokemon.id == pokemon_id)
        .first()
    )
    if not pokemon:
        raise HTTPException(status_code=404, detail="Pokémon introuvable")

    response = PokemonResponse.model_validate(pokemon).model_dump()
    set_cache(cache_key, response)
    return response


def _area_name_fr(client: httpx.Client, slug: str) -> str | None:
    cache_key = f"area-fr:{slug}"
    if cached := get_cached(cache_key):
        return cached.get("name")
    resp = client.get(f"{POKEAPI}/location-area/{slug}/", timeout=5.0)
    if resp.status_code != 200:
        return None
    fr = next(
        (
            n["name"]
            for n in resp.json().get("names", [])
            if n["language"]["name"] == "fr"
        ),
        None,
    )
    set_cache(cache_key, {"name": fr}, ttl=60 * 60 * 24 * 30)
    return fr


@router.get(
    "/{pokemon_id}/encounters",
    responses={
        404: {"description": "Pokémon introuvable"},
        429: {"description": "Trop de requêtes — réessayez dans 60s"},
    },
)
@limiter.limit(RATE_LIMIT)
def get_encounters(request: Request, pokemon_id: int):
    cache_key = f"encounters:{pokemon_id}"
    if cached := get_cached(cache_key):
        return cached

    with httpx.Client(timeout=10.0) as client:
        resp = client.get(f"{POKEAPI}/pokemon/{pokemon_id}/encounters")
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Pokémon introuvable")
        resp.raise_for_status()

        encounters = []
        for area in resp.json():
            area_name = area["location_area"]["name"]
            for version_info in area["version_details"]:
                game = version_info["version"]["name"]
                for detail in version_info["encounter_details"]:
                    encounters.append(
                        {
                            "location_area": area_name,
                            "game": game,
                            "method": detail["method"]["name"],
                            "chance": detail["chance"],
                            "min_level": detail["min_level"],
                            "max_level": detail["max_level"],
                            "conditions": [
                                c["name"] for c in detail["condition_values"]
                            ],
                        }
                    )

        unique_slugs = {e["location_area"] for e in encounters}
        name_fr_map = {slug: _area_name_fr(client, slug) for slug in unique_slugs}

    for e in encounters:
        fr = name_fr_map.get(e["location_area"])
        if fr:
            e["location_area_fr"] = fr

    result = {"encounters": encounters, "has_encounters": bool(encounters)}
    set_cache(cache_key, result)
    return result
